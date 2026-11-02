<img src="assets/orelyn-mark.svg" width="64" alt="ORELYN original strata loop mark">

# ORELYN

**Local-first public data registry, incremental sync and provenance.**  
本地优先的公开数据注册、增量同步与溯源工具。

ORELYN helps you inspect source metadata before downloading, monitor changes with conditional HTTP requests, resume partial files safely, and preserve verifiable provenance for geospatial research.

It is an independent product. No domain, account, database or cloud service is required for the offline document.

## What it does

- **Source registry:** 8 real public-data sources with access and license metadata.
- **Incremental monitoring:** ETag / Last-Modified conditional requests and 304 handling.
- **Safe resume:** Range continuation, `.part` files and safe restart when Range is ignored.
- **Integrity evidence:** SHA-256 for complete files, local state snapshots and previous-version archives.
- **License gates:** sources requiring license or query review are excluded from automatic downloads.
- **Offline presentation:** standalone HTML with registry filters, source details, attribution copy and local-state import.
- **Low-frequency checks:** an explicit `watch` command with a minimum one-hour interval, not a hosted crawler.

## Open the offline document

Open **`ORELYN.html`** directly in a browser. Styles, registry data, scripts and the original icon are embedded in that single file.

直接双击 `ORELYN.html` 即可离线查看数据注册表、许可信息、溯源证据和本地同步状态，无需部署。

## CLI

Requires **Python 3.11+**. Runtime code uses only the Python standard library.

```bash
# Check registered endpoint availability
python cli.py check

# Incrementally sync one public, license-cleared source
python cli.py sync --source ga-particle-size

# Show local synchronization evidence
python cli.py status

# Start low-frequency monitoring (Ctrl+C to stop)
python cli.py watch --interval-hours 24
```

Run these commands from the repository root. Downloaded originals, partial files, versions and `registry-state.json` are written under `data/` and are intentionally ignored by Git.

## Registry model

Each source in `registry.json` records:

- publisher and dataset identity;
- official endpoint and access method;
- license name and license URL;
- attribution requirement;
- evidence date and review cycle;
- whether incremental download is enabled;
- whether bounded, filter-specific queries are required.

**Public availability is not treated as unrestricted usage permission.** License metadata supports review but does not replace the provider's current terms or legal advice.

## Build the standalone HTML

```bash
python build.py
```

`build.py` packages the page, styles, registry and original icon into a self-contained `ORELYN.html` with an offline Content Security Policy.

## Validation

```bash
python -m unittest discover -s tests -v
```

Current verification includes:

- 7 sync and license tests covering resume, ignored Range, 304, previous-version archives and license gates;
- real Geoscience Australia synchronization: **1,642,356 bytes**, with a second run reported as `unchanged`;
- offline desktop and mobile rendering, source filtering, detail dialogs and language switching;
- standalone-document initialization and release archive integrity checks.

## Repository structure

```text
ORELYN.html           Self-contained offline document
index.html            Source page for the standalone build
app.js                Registry UI, filters, dialogs and local-state import
registry.json         Canonical source and license metadata
registry.js           Browser-ready registry generated from JSON
cli.py                Checks, incremental sync, resume and watch
build.py              Standalone-document builder
assets/               Original product and author artwork
tests/                Sync tests and offline UI checks
```

`data/` and `dist/` are local-only working/output directories and are not committed.

## Release

- Repository: https://github.com/lucia-lee-geo/orelyn
- Release: https://github.com/lucia-lee-geo/orelyn/releases/tag/v1.0.0
- Local package: https://github.com/lucia-lee-geo/orelyn/releases/download/v1.0.0/ORELYN-local.zip

## Author

**LUCIA LEE (李镜馨)**  
**独立研究与软件开发｜空间数据**  
Independent Research & Software Development | Geospatial Data  
Contact: lijingxin.geo@outlook.com

## License and reuse

No OSI license has been selected for this repository. Source availability does not imply permission for unrestricted copying, redistribution or commercial reuse. Dataset licenses and attribution duties remain with their respective providers and are recorded in `registry.json`.
