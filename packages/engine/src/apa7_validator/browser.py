"""Browser entrypoint — Pyodide calls these from JS.

Existence checks (CrossRef, Unpaywall, OpenLibrary, URL liveness) are disabled
in this module because the browser cannot satisfy CORS for those APIs.
"""

from __future__ import annotations

import json
import uuid
from bisect import bisect_right

from .api import Format, annotate_docx, validate_async
from .clients import Clients
from .extractors import DocxExtractor, PdfExtractor
from .models import Report
from .render import render_json

_REPORT_CACHE: dict[str, tuple[Report, bytes | None]] = {}


def _extract_text(source: bytes | str, format: Format) -> str:
    """Extract plain text from source bytes/str for line-number computation."""
    if format == "text":
        if isinstance(source, bytes):
            return source.decode("utf-8")
        return source
    if format == "docx":
        if isinstance(source, str):
            raise TypeError("DOCX requires bytes, got str")
        return DocxExtractor().extract(source).text
    if format == "pdf":
        if isinstance(source, str):
            raise TypeError("PDF requires bytes, got str")
        return PdfExtractor().extract(source).text
    raise ValueError(f"unknown format: {format!r}")


async def run(source: bytes | str, format: Format) -> str:
    """Run validation in dry-run mode and cache the Report for later annotation.

    Returns a JSON string: {"job_id": "...", "json": <the report's render_json>}.
    The job_id is used by `annotate(...)` to recover the Report.
    """
    # Clear previous cache — single-user browser session, only one active job.
    _REPORT_CACHE.clear()

    # Extract text to compute 1-based line numbers for each issue.
    text = _extract_text(source, format)
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    report = await validate_async(source, format, clients=Clients.dry_run())
    job_id = str(uuid.uuid4())
    src_bytes = source if isinstance(source, bytes) else None
    _REPORT_CACHE[job_id] = (report, src_bytes)

    payload = json.loads(render_json(report))
    for iss in payload["issues"]:
        offset = iss["position"]["start"]
        iss["line"] = bisect_right(line_starts, offset)

    return json.dumps(
        {
            "job_id": job_id,
            "report": payload,
        }
    )


def annotate(job_id: str) -> bytes:
    """Look up the cached Report for `job_id` and return annotated DOCX bytes."""
    if job_id not in _REPORT_CACHE:
        raise KeyError(f"no cached report for job_id={job_id!r}")
    report, src_bytes = _REPORT_CACHE[job_id]
    return annotate_docx(src_bytes, report)
