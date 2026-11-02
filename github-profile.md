# ORELYN GitHub Publication Profile

## Public identity

**LUCIA LEE (李镜馨)**  
**Independent Research & Software Development | Geospatial Data**  
独立研究与软件开发｜空间数据  
Contact: lijingxin.geo@outlook.com

Do not invent an employer, academic title, seniority claim or company affiliation.

## Original profile avatar

Use `assets/lucia-lee-avatar-512.png` as the standard platform avatar. The original tilted mirror frame references 镜, with reflected L forms, a gold origin light and hand-drawn terrain curves. Editable master: `assets/lucia-lee-avatar.svg`. 1024px and 256px PNG variants are also included.

## Repository

- Name: `orelyn`
- Suggested title: `ORELYN — Local-first data registry & incremental sync`
- Description: `Local-first public data registry, license metadata, incremental downloads and provenance for geospatial research.`
- Visibility: Public (source available; do not label it as an OSI-licensed open-source project unless a license is deliberately chosen).
- Topics: `geospatial`, `data-governance`, `provenance`, `python`, `data-etl`, `ogc`, `resumable-download`

## Repository contents

Include:

- `index.html`, `styles.css`, `app.js`, `registry.js`, `registry.json`
- `ORELYN.html` (self-contained offline document)
- `cli.py`, `build.py`
- `assets/orelyn-mark.svg`
- `tests/`
- `orelyn-desktop.png`, `orelyn-mobile.png` for documentation
- `.gitignore` excluding `data/`, `dist/`, caches, local credentials and OS files

Do not include:

- `data/` or downloaded source copies
- `dist/`
- `.env`, credentials, tokens or account metadata
- unrelated GEORIN project files

## Release 1.0.0

Title: `ORELYN 1.0.0 — Offline registry and resumable local sync`

Release asset: `dist/ORELYN-local.zip`

Release notes:

- Eight real public-data source records with separate license and access metadata
- Offline standalone HTML registry and evidence viewer
- ETag / Last-Modified conditional monitoring
- Range resume with safe handling for ignored Range responses
- SHA-256 for complete files and archived previous versions
- Read-only completed originals and local registry-state snapshots
- Seven sync/license tests plus desktop/mobile offline checks
- Real GA synchronization verified: 1,642,356 bytes; second run unchanged

Boundaries:

- No domain, account, database or cloud service is required for the offline document.
- `watch` is a user-started low-frequency loop, not a hosted crawler.
- License-pending sources are excluded from automatic downloads.
- Public availability is not presented as unrestricted usage permission.

Author: **LUCIA LEE (李镜馨)**  
Tag: **独立研究与软件开发｜空间数据**
