from __future__ import annotations

import re

from ...models import Position, Reference, ReferenceType
from .journal import parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?|n\.d\.(?:-[a-z])?)(?:,\s*[^)]+)?\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?:(?P<container>[A-Z][^.]+?)\.\s*)?
    (?P<url>https?://\S+)\s*$
    """,
    re.VERBOSE,
)


def try_parse_website(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.WEBSITE,
        authors=parse_authors(m.group("authors").rstrip(".")),
        year=m.group("year"),
        title=m.group("title").strip(),
        container=m.group("container").strip() if m.group("container") else None,
        url=m.group("url"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
