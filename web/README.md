# Browser MVP

A static site that runs `apa7_validator` entirely in the browser via Pyodide.

## Dev loop

```
cd "/Users/aaron/codebase/active/APA7-reference checker"
uv build --wheel packages/engine
cp dist/apa7_validator-*.whl web/dist/
cd web
python3 -m http.server 8000
# open http://localhost:8000
```

The first load downloads Pyodide (~10 MB) from the jsDelivr CDN. After that the browser caches it.

## Deploy

Pushes to `main` that touch `web/**` or `packages/engine/**` trigger
`.github/workflows/pages.yml`, which rebuilds the wheel, copies it into
`web/dist/`, and uploads `web/` to GitHub Pages.

GitHub Pages source must be set to "GitHub Actions" in repo settings (one-time setup).
