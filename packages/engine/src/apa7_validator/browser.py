"""Browser entrypoint — Pyodide calls these from JS.

Existence checks (CrossRef, Unpaywall, OpenLibrary, URL liveness) are disabled
in this module because the browser cannot satisfy CORS for those APIs.
"""

from __future__ import annotations

import json
import uuid

from .api import Format, annotate_docx, validate_async
from .clients import Clients
from .models import Report
from .render import render_json

_REPORT_CACHE: dict[str, tuple[Report, bytes | None]] = {}


async def run(source: bytes | str, format: Format) -> str:
    """Run validation in dry-run mode and cache the Report for later annotation.

    Returns a JSON string: {"job_id": "...", "json": <the report's render_json>}.
    The job_id is used by `annotate(...)` to recover the Report.
    """
    # Clear previous cache — single-user browser session, only one active job.
    _REPORT_CACHE.clear()

    report = await validate_async(source, format, clients=Clients.dry_run())
    job_id = str(uuid.uuid4())
    src_bytes = source if isinstance(source, bytes) else None
    _REPORT_CACHE[job_id] = (report, src_bytes)

    return json.dumps(
        {
            "job_id": job_id,
            "report": json.loads(render_json(report)),
        }
    )


def annotate(job_id: str) -> bytes:
    """Look up the cached Report for `job_id` and return annotated DOCX bytes."""
    if job_id not in _REPORT_CACHE:
        raise KeyError(f"no cached report for job_id={job_id!r}")
    report, src_bytes = _REPORT_CACHE[job_id]
    return annotate_docx(src_bytes, report)
