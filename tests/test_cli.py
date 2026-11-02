from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli  # noqa: E402

PAYLOAD = bytes(range(256)) * 1024


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        return

    def _headers(self, status: int, length: int, **headers) -> None:
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name.replace("_", "-"), str(value))
        self.send_header("Content-Length", str(length))
        self.end_headers()

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path == "/check.csv":
            self._headers(405, 0)
            return
        if self.headers.get("If-None-Match") == '"v1"':
            self._headers(304, 0)
            return
        self._headers(200, len(PAYLOAD), ETag='"v1"', Last_Modified="Sun, 01 Nov 2026 00:00:00 GMT")

    def do_GET(self) -> None:  # noqa: N802
        if self.headers.get("If-None-Match") == '"v1"':
            self._headers(304, 0)
            return
        if self.path == "/full.csv":
            self._headers(200, len(PAYLOAD), ETag='"v1"')
            self.wfile.write(PAYLOAD)
            return
        start = 0
        range_header = self.headers.get("Range", "")
        if range_header.startswith("bytes="):
            start = int(range_header.removeprefix("bytes=").split("-", 1)[0])
        body = PAYLOAD[start:]
        if start:
            self._headers(206, len(body), Content_Range=f"bytes {start}-{len(PAYLOAD)-1}/{len(PAYLOAD)}", ETag='"v1"')
        else:
            self._headers(200, len(body), ETag='"v1"')
        self.wfile.write(body)


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=5)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def source(self, path: str = "/resume.csv", source_id: str = "test-source") -> dict:
        return {
            "id": source_id,
            "endpoint": self.base_url + path,
            "filename": "source.csv",
            "syncEnabled": True,
            "licenseClass": "open",
        }

    def test_resume_download_hashes_existing_and_new_bytes(self) -> None:
        source = self.source()
        partial_dir = self.data_dir / "raw" / source["id"]
        partial_dir.mkdir(parents=True)
        partial = partial_dir / "source.csv.part"
        partial.write_bytes(PAYLOAD[:100])
        result = cli.download_source(source, self.data_dir)
        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["resumed"])
        self.assertEqual(result["bytes"], len(PAYLOAD))
        self.assertEqual(result["sha256"], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertEqual((partial_dir / "source.csv").read_bytes(), PAYLOAD)

    def test_range_ignored_restarts_without_duplication(self) -> None:
        source = self.source("/full.csv")
        partial_dir = self.data_dir / "raw" / source["id"]
        partial_dir.mkdir(parents=True)
        (partial_dir / "source.csv.part").write_bytes(PAYLOAD[:100])
        result = cli.download_source(source, self.data_dir)
        self.assertFalse(result["resumed"])
        self.assertEqual(result["bytes"], len(PAYLOAD))
        self.assertEqual((partial_dir / "source.csv").read_bytes(), PAYLOAD)

    def test_unchanged_response_skips_download(self) -> None:
        source = self.source()
        destination = self.data_dir / "raw" / source["id"] / "source.csv"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(PAYLOAD)
        cli.save_state(self.data_dir, {"downloads": {source["id"]: {"status": "complete", "etag": '"v1"', "sha256": hashlib.sha256(PAYLOAD).hexdigest()}}})
        result = cli.download_source(source, self.data_dir)
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse((self.data_dir / "versions").exists())

    def test_new_version_archives_previous_original(self) -> None:
        source = self.source()
        destination = self.data_dir / "raw" / source["id"] / "source.csv"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"previous-version")
        cli.save_state(self.data_dir, {"downloads": {source["id"]: {"status": "complete", "etag": '"old"', "sha256": "old"}}})
        result = cli.download_source(source, self.data_dir)
        self.assertEqual(result["status"], "complete")
        archives = list((self.data_dir / "versions" / source["id"]).glob("*-source.csv"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].read_bytes(), b"previous-version")

    def test_license_gate_blocks_automatic_download(self) -> None:
        source = self.source()
        source["syncEnabled"] = False
        with self.assertRaises(ValueError):
            cli.download_source(source, self.data_dir)

    def test_head_failure_falls_back_to_bounded_get(self) -> None:
        result = cli.check_source(self.source("/check.csv"))
        self.assertEqual(result["health"], "available")

    def test_registry_contains_verified_license_metadata(self) -> None:
        registry = cli.load_registry()
        self.assertEqual(len(registry["sources"]), 8)
        self.assertEqual(sum(source["syncEnabled"] for source in registry["sources"]), 4)
        self.assertEqual(sum(source["licenseClass"] == "review" for source in registry["sources"]), 1)
        for source in registry["sources"]:
            self.assertTrue(source["endpoint"].startswith("https://"))
            self.assertTrue(source["licenseUrl"].startswith("https://"))
            self.assertTrue(source["attribution"])


if __name__ == "__main__":
    unittest.main()
