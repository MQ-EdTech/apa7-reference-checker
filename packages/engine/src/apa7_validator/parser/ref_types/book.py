from __future__ import annotations

import re

from ...models import Position, Reference, ReferenceType
from .journal import parse_authors  # reuse author parsing

# The journal tail pattern includes an en-dash (U+2013) which APA style uses
# for page ranges. We build it via chr() to avoid a literal ambiguous character
# that ruff would flag as RUF001.
_EN_DASH = chr(0x2013)

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?|n\.d\.(?:-[a-z])?)(?:,\s*[^)]+)?\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?P<publisher>[A-Z][^.]+?)\.?\s*
    (?:
        (?:https?://(?:dx\.)?doi\.org/|doi:\s*)(?P<doi>\S+)
      |
        (?P<url>https?://\S+)
    )?\s*$
    """,
    re.VERBOSE,
)

_JOURNAL_TAIL = re.compile(r",\s*\d+(\([^)]+\))?,\s*[\d\-" + _EN_DASH + r",\s]+")


def try_parse_book(raw: str, position_start: int) -> Reference | None:
    if _JOURNAL_TAIL.search(raw):
        return None
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK,
        authors=parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        publisher=m.group("publisher").strip(),
        doi=m.group("doi"),
        url=m.group("url"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
