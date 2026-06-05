from __future__ import annotations

import re

from ...models import Author, Position, Reference, ReferenceType

# Journal article shape (loose):
#   <authors> (<year>). <title>. <Journal>, <volume>(<issue>), <pages>. [doi/url]
#
# The pages character class includes the en-dash (U+2013) which APA style uses
# for page ranges. We build it via chr() to avoid a literal ambiguous character
# that ruff would flag as RUF001.
_EN_DASH = chr(0x2013)
_PAGES_CHARS = r"\d\-" + _EN_DASH + r",\s"

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?P<container>[A-Z][^,]+),\s*
    (?P<volume>\d+)
    (?:\((?P<issue>[^)]+)\))?
    (?:,\s*(?P<pages>["""
    + _PAGES_CHARS
    + r"""]+))?
    \.?\s*
    (?:https?://(?:dx\.)?doi\.org/(?P<doi>\S+))?
    """,
    re.VERBOSE,
)


def _parse_authors(raw: str) -> list[Author]:
    # APA author lists: "Smith, J., Jones, A., & Lee, B."
    # Split on ", &" or ", " — group "Last, F. M." pairs.
    parts = [p.strip().rstrip(",") for p in re.split(r",\s*&\s*|,\s+", raw) if p.strip()]
    authors: list[Author] = []
    i = 0
    while i < len(parts):
        family = parts[i]
        initials = (
            parts[i + 1] if i + 1 < len(parts) and re.match(r"^[A-Z]\.", parts[i + 1]) else ""
        )
        authors.append(Author(family=family, given_initials=initials))
        i += 2 if initials else 1
    return authors


def try_parse_journal(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        container=m.group("container").strip(),
        volume=m.group("volume"),
        issue=m.group("issue"),
        pages=m.group("pages").strip() if m.group("pages") else None,
        doi=m.group("doi"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
