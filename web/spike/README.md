# Phase 0 Pyodide spike

Proves the engine wheel imports and runs under Pyodide in the browser. Not the
real site — `web/` (one level up) is for the actual MVP.

## Run

```
cd "/Users/aaron/codebase/active/APA7-reference checker"
uv build --wheel packages/engine
cp dist/apa7_validator-*.whl web/spike/dist/
cd web/spike
python3 -m http.server 8000
# open http://localhost:8000 in a browser
```

Note: `uv build --wheel packages/engine` places the wheel at the workspace root
`dist/` (not `packages/engine/dist/`), so copy from there.

The page shows progress, then either the JSON report or the failure mode (likely
`RuntimeError: asyncio.run() cannot be called from a running event loop` — that's
expected, and Phase 1 fixes it).
