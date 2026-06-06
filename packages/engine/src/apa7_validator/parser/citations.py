# ruff: noqa: RUF001  (regex char classes intentionally include en-dash U+2013 literal)
from __future__ import annotations

import re

from ..models import Citation, Position

# A single citation form INSIDE the parentheses (no outer parens):
#   "Author, YYYY"  OR  "A & B, YYYY"  OR  "Author et al., YYYY"
#   plus optional ", p. N" / ", pp. N-M"
#   plus optional "YYYY, as cited in OtherAuthor, YYYY"
_INNER_RE = re.compile(
    r"""
    ^\s*
    (?P<authors>[^(),;]+?(?:\s*&\s*[^(),;]+?)?(?:\s+et\s+al\.)?)
    ,\s*
    (?:
        (?P<sec_year>\d{4}[a-z]?)
        ,\s*as\s+cited\s+in\s+
        (?P<cited_author>[^,)]+?)
        ,\s*(?P<cited_year>\d{4}[a-z]?)
    |
        (?P<year>\d{4}[a-z]?)
        (?:,\s*pp?\.\s*(?P<page>[\d\-–]+))?
    )
    \s*$
    """,
    re.VERBOSE,
)

# Locator for top-level parenthetical groups (no nested parens supported).
_PAREN_GROUP_RE = re.compile(r"\(([^()]+)\)")

# Narrative: Smith (2020) or Smith and Jones (2020) or Smith et al. (2020)
_NARRATIVE_RE = re.compile(
    r"""
    \b
    (?P<authors>[A-Z][a-zA-Z\-']+(?:\s+(?:and|&)\s+[A-Z][a-zA-Z\-']+)?(?:\s+et\s+al\.)?)
    \s+
    \(
    (?P<year>\d{4}[a-z]?)
    (?:,\s*pp?\.\s*(?P<page>[\d\-–]+))?
    \)
    """,
    re.VERBOSE,
)


def _split_authors(raw: str) -> list[str]:
    raw = raw.strip()
    if "et al." in raw:
        return [raw]
    parts = re.split(r"\s*(?:&|and)\s*", raw)
    return [p.strip() for p in parts if p.strip()]


def _parse_inner(piece: str, *, paren_start: int, paren_end: int) -> Citation | None:
    m = _INNER_RE.match(piece)
    if m is None:
        return None
    if m.group("cited_author") is not None:
        return Citation(
            raw=f"({piece.strip()})",
            authors=[m.group("cited_author").strip()],
            year=m.group("cited_year"),
            page=None,
            narrative=False,
            secondary_source_author=_split_authors(m.group("authors"))[0],
            position=Position(start=paren_start, end=paren_end),
        )
    return Citation(
        raw=f"({piece.strip()})",
        authors=_split_authors(m.group("authors")),
        year=m.group("year"),
        page=m.group("page"),
        narrative=False,
        position=Position(start=paren_start, end=paren_end),
    )


def parse_citations(text: str) -> list[Citation]:
    cits: list[Citation] = []

    for m in _PAREN_GROUP_RE.finditer(text):
        inner = m.group(1)
        paren_start, paren_end = m.start(), m.end()
        # Split semicolon-separated multi-citations.
        pieces = re.split(r"\s*;\s*", inner)
        for piece in pieces:
            cit = _parse_inner(piece, paren_start=paren_start, paren_end=paren_end)
            if cit is not None:
                cits.append(cit)

    for m in _NARRATIVE_RE.finditer(text):
        # Avoid double-counting if a parenthetical group already covered the same span.
        if any(c.position.start <= m.start() < c.position.end for c in cits):
            continue
        cits.append(
            Citation(
                raw=m.group(0),
                authors=_split_authors(m.group("authors")),
                year=m.group("year"),
                page=m.group("page"),
                narrative=True,
                position=Position(start=m.start(), end=m.end()),
            )
        )

    cits.sort(key=lambda c: c.position.start)
    return cits
