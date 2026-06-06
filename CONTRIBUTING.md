# Contributing

## Setup

```bash
uv sync --all-packages --all-extras
uv run pre-commit install
```

## Testing

```bash
uv run pytest packages/engine/tests       # engine
uv run pytest packages/cli/tests          # cli
uv run pyright packages/engine/src packages/cli/src
uv run ruff check . && uv run ruff format --check .
```

## Recording new HTTP cassettes

The existence-check tests use VCR cassettes under
`packages/engine/tests/fixtures/cassettes/`. To record new ones:

```bash
RECORD_MODE=new_episodes uv run pytest packages/engine/tests/clients -v
```

Commit the resulting `.yaml` files. CI runs with `RECORD_MODE=none` and will
fail if a cassette is missing.

## Privacy rules

- **Never commit real student work** to test fixtures. Synthetic data only.
- **Never log essay text**. The `safe_log()` helper enforces a field allowlist.
- **Never add a parameter named `text`, `essay`, `body`, `content`, or
  `extracted_text` to any client function.** A structural test
  (`tests/test_structural_guarantees.py`) guards this in CI.

## Commit style

Conventional commits (`feat:`, `fix:`, `test:`, `refactor:`, `chore:`,
`docs:`). One logical change per commit; commit frequently.
