#!/usr/bin/env python3
"""ORELYN local-first source checks and incremental, resumable downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = ROOT / "data"
USER_AGENT = "ORELYN/1.0 (local-first provenance registry)"
CHUNK_SIZE = 1024 * 1024


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_registry() -> dict:
    return json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))


def sources(registry: dict, source_id: str | None) -> list[dict]:
    selected = registry["sources"]
    if source_id is None:
        return selected
    matches = [source for source in selected if source["id"] == source_id]
    if not matches:
        raise ValueError(f"Unknown source id: {source_id}")
    return matches


def load_state(data_dir: Path) -> dict:
    path = data_dir / "registry-state.json"
    if not path.is_file():
        return {"schemaVersion": "1.0.0", "generatedAt": utc_now(), "checks": {}, "downloads": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    state.setdefault("checks", {})
    state.setdefault("downloads", {})
    return state


def save_state(data_dir: Path, state: dict) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    state["generatedAt"] = utc_now()
    temporary = data_dir / "registry-state.json.part"
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, data_dir / "registry-state.json")


def request(url: str, *, method: str = "GET", offset: int = 0, previous: dict | None = None, timeout: int = 30) -> urllib.response.addinfourl:
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    if previous:
        if previous.get("etag"):
            headers["If-None-Match"] = previous["etag"]
        if previous.get("lastModified"):
            headers["If-Modified-Since"] = previous["lastModified"]
    req = urllib.request.Request(url, method=method, headers=headers)
    return urllib.request.urlopen(req, timeout=timeout)


def response_metadata(response, checked_at: str) -> dict:
    length = response.headers.get("Content-Length")
    return {
        "checkedAt": checked_at,
        "httpStatus": response.status,
        "etag": response.headers.get("ETag", ""),
        "lastModified": response.headers.get("Last-Modified", ""),
        "contentLength": int(length) if length and length.isdigit() else None,
    }


def check_source(source: dict) -> dict:
    checked_at = utc_now()
    try:
        try:
            response = request(source["endpoint"], method="HEAD", timeout=20)
        except urllib.error.HTTPError as error:
            if error.code not in {400, 405, 501}:
                raise
            response = request(source["endpoint"], timeout=20)
        with response:
            metadata = response_metadata(response, checked_at)
            if response.status == 304:
                metadata["health"] = "unchanged"
            else:
                metadata["health"] = "available"
            return metadata
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"checkedAt": checked_at, "health": "unavailable", "error": str(error)[:180]}


def check(registry: dict, data_dir: Path, source_id: str | None) -> None:
    state = load_state(data_dir)
    for source in sources(registry, source_id):
        result = check_source(source)
        state["checks"][source["id"]] = result
        print(f"{source['id']}: {result['health']}")
    save_state(data_dir, state)


def archive_existing(destination: Path, source_id: str, data_dir: Path) -> None:
    if not destination.is_file():
        return
    archive_dir = data_dir / "versions" / source_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive = archive_dir / f"{stamp}-{destination.name}"
    counter = 1
    while archive.exists():
        archive = archive_dir / f"{stamp}-{counter}-{destination.name}"
        counter += 1
    shutil.copy2(destination, archive)


def download_source(source: dict, data_dir: Path) -> dict:
    if not source["syncEnabled"] or source["licenseClass"] != "open":
        raise ValueError(f"Automatic download is disabled for {source['id']}: license or query review required")
    destination_dir = data_dir / "raw" / source["id"]
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source["filename"]
    partial = destination.with_suffix(destination.suffix + ".part")
    previous = load_state(data_dir)["downloads"].get(source["id"], {})

    if destination.is_file() and previous.get("status") == "complete":
        try:
            with request(source["endpoint"], method="HEAD", previous=previous, timeout=20) as response:
                if response.status == 304:
                    return {"status": "unchanged", "bytes": destination.stat().st_size, "sha256": previous.get("sha256", "")}
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

    offset = partial.stat().st_size if partial.is_file() else 0
    resumed = offset > 0
    try:
        response = request(source["endpoint"], offset=offset, previous={} if offset else previous, timeout=45)
    except urllib.error.HTTPError as error:
        if error.code == 304 and destination.is_file():
            return {"status": "unchanged", "bytes": destination.stat().st_size, "sha256": previous.get("sha256", "")}
        if error.code == 416 and offset:
            partial.unlink()
            return download_source(source, data_dir)
        raise

    with response:
        if response.status == 304 and destination.is_file():
            return {"status": "unchanged", "bytes": destination.stat().st_size, "sha256": previous.get("sha256", "")}
        if offset and response.status != 206:
            print(f"{source['id']}: server ignored Range; restarting safely from byte zero")
            offset = 0
            resumed = False
            response.close()
            response = request(source["endpoint"], timeout=45)
        mode = "ab" if offset else "wb"
        digest = hashlib.sha256()
        if offset:
            with partial.open("rb") as existing:
                for chunk in iter(lambda: existing.read(CHUNK_SIZE), b""):
                    digest.update(chunk)
        downloaded = offset
        with partial.open(mode) as output:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                downloaded += len(chunk)

    if downloaded == 0:
        raise RuntimeError(f"{source['id']}: empty response")
    archive_existing(destination, source["id"], data_dir)
    os.replace(partial, destination)
    os.chmod(destination, 0o444)
    result = {
        "status": "complete",
        "filename": source["filename"],
        "bytes": downloaded,
        "sha256": digest.hexdigest(),
        "etag": response.headers.get("ETag", ""),
        "lastModified": response.headers.get("Last-Modified", ""),
        "completedAt": utc_now(),
        "resumed": resumed,
    }
    state = load_state(data_dir)
    state["downloads"][source["id"]] = result
    save_state(data_dir, state)
    return result


def sync(registry: dict, data_dir: Path, source_id: str | None) -> None:
    for source in sources(registry, source_id):
        if not source["syncEnabled"]:
            print(f"{source['id']}: skipped (query-only or license review)")
            continue
        try:
            result = download_source(source, data_dir)
            print(f"{source['id']}: {result['status']} · {result['bytes']} bytes · resumed={result.get('resumed', False)}")
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError, ValueError) as error:
            print(f"{source['id']}: incomplete · {error}", file=sys.stderr)


def show_status(data_dir: Path) -> None:
    state = load_state(data_dir)
    print(f"State generated: {state['generatedAt']}")
    print(f"Endpoint checks: {len(state['checks'])}")
    print(f"Download records: {len(state['downloads'])}")
    for source_id, record in state["downloads"].items():
        print(f"{source_id}: {record['status']} · {record.get('bytes', 0)} bytes · {record.get('sha256', '')}")


def build_registry_js() -> None:
    registry = load_registry()
    (ROOT / "registry.js").write_text(
        "window.ORELYN_REGISTRY = " + json.dumps(registry, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Registry {registry['registryVersion']} written to registry.js")


def watch(registry: dict, data_dir: Path, source_id: str | None, interval_hours: float) -> None:
    if interval_hours < 1:
        raise ValueError("interval-hours must be at least 1 to avoid high-frequency crawling")
    print(f"Watch started with a {interval_hours:g}-hour interval. Press Ctrl+C to stop.")
    try:
        while True:
            check(registry, data_dir, source_id)
            sync(registry, data_dir, source_id)
            time.sleep(interval_hours * 3600)
    except KeyboardInterrupt:
        print("Watch stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check", "cite", "list", "status", "sync", "watch"])
    parser.add_argument("--source", help="Source id from registry.json")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--interval-hours", type=float, default=24.0)
    args = parser.parse_args()
    registry = load_registry()
    try:
        if args.command == "build":
            build_registry_js()
        elif args.command == "check":
            check(registry, args.data_dir, args.source)
        elif args.command == "sync":
            sync(registry, args.data_dir, args.source)
        elif args.command == "status":
            show_status(args.data_dir)
        elif args.command == "watch":
            watch(registry, args.data_dir, args.source, args.interval_hours)
        elif args.command == "list":
            for source in registry["sources"]:
                print(f"{source['id']}: {source['license']} · sync={source['syncEnabled']} · {source['endpoint']}")
        elif args.command == "cite":
            selected = sources(registry, args.source)
            if len(selected) != 1:
                raise ValueError("cite requires --source with exactly one id")
            source = selected[0]
            print(f"{source['name']} — {source['attribution']}. {source['license']}. {source['endpoint']}")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
