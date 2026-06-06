from __future__ import annotations

import re

from ...models import Position, Reference, ReferenceType
from .journal import parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.()]+?)\.?\s*
    (?:\(Report\s+No\.\s*(?P<report_no>[^)]+)\)\.?\s*)?
    (?P<publisher>[^.]+?)\.?\s*
    (?:(?:https?://(?:dx\.)?doi\.org/|doi:\s*)(?P<doi>\S+))?\s*$
    """,
    re.VERBOSE,
)

_REPORT_HINT = re.compile(r"(?i:\b(?:report|bureau|department)\b)|\b(?:OECD|UN|WHO)\b")


def try_parse_report(raw: str, position_start: int) -> Reference | None:
    if not _REPORT_HINT.search(raw):
        return None
    m = _RE.match(raw.strip())
    if not m:
        return None
    extras: dict[str, str] = {}
    if m.group("report_no"):
        extras["report_number"] = m.group("report_no").strip()
    return Reference(
        raw=raw,
        ref_type=ReferenceType.REPORT,
        authors=parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        publisher=m.group("publisher").strip(),
        doi=m.group("doi"),
        extras=extras,
        position=Position(start=position_start, end=position_start + len(raw)),
    )
