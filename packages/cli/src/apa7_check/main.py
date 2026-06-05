from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from apa7_validator import validate
from apa7_validator.clients import Clients

from apa7_check.render import render_human, render_json

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    return {".docx": "docx", ".pdf": "pdf"}.get(suffix, "text")


@app.command()
def main(
    file: Annotated[Path, typer.Argument(exists=True, readable=True)],
    json_output: Annotated[bool, typer.Option("--json", help="emit JSON")] = False,
) -> None:
    """Validate APA 7 references in FILE and print a human-readable report."""
    fmt = _detect_format(file)
    source: bytes | str
    source = file.read_text(encoding="utf-8") if fmt == "text" else file.read_bytes()
    report = validate(source, fmt, clients=Clients.dry_run())  # type: ignore[arg-type]
    if json_output:
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_human(report))
