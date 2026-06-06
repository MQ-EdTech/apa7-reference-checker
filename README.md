# APA 7 Reference Checker

Validates APA 7 references and in-text citations in `.docx`, `.pdf`, and plain-text essays.

This repository contains:

- `packages/engine` — `apa7_validator`, the pure-Python validation engine.
- `packages/cli` — `apa7-check`, a command-line frontend.

## Quick start

```bash
uv sync --all-packages --all-extras
uv run apa7-check packages/engine/tests/fixtures/docx/sample_essay.docx
uv run apa7-check essay.docx --annotate annotated.docx
uv run apa7-check essay.txt --json
```

## Privacy

The engine never sends essay text to any third-party service. The only data
that leaves the box is the set of public identifiers required for lookup:
DOIs (to CrossRef and Unpaywall) and ISBNs (to OpenLibrary). See
`docs/superpowers/specs/2026-06-04-apa7-reference-checker-design.md` §9 for
the full privacy posture.

## Status

Engine + CLI (this plan): complete. API + worker (FastAPI + arq), LTI 1.3
endpoints, and the SPA frontend are planned as separate sub-projects.
