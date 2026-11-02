#!/usr/bin/env python3
"""Build ORELYN.html as a fully self-contained offline document."""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    registry = (ROOT / "registry.js").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    icon = base64.b64encode((ROOT / "assets" / "orelyn-mark.svg").read_bytes()).decode("ascii")

    html = html.replace(
        '<link rel="icon" href="assets/orelyn-mark.svg" type="image/svg+xml">',
        f'<link rel="icon" href="data:image/svg+xml;base64,{icon}" type="image/svg+xml">',
    )
    html = html.replace('src="assets/orelyn-mark.svg"', f'src="data:image/svg+xml;base64,{icon}"')
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>\n{css}\n</style>")
    html = html.replace('<script src="registry.js" defer></script>', f"<script>\n{registry}\n</script>")
    html = html.replace('<script src="app.js" defer></script>', f"<script>\n{app}\n</script>")

    csp = (
        '<meta http-equiv="Content-Security-Policy" content="default-src \'self\' data:; '
        "img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; font-src 'self'; "
        'object-src \'none\'; base-uri \'none\'; form-action \'self\'">'
    )
    html = html.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', f'<meta name="viewport" content="width=device-width, initial-scale=1">\n  {csp}')

    output = ROOT / "ORELYN.html"
    output.write_text(html, encoding="utf-8")
    print(f"Standalone offline document built: {output}")


if __name__ == "__main__":
    main()
