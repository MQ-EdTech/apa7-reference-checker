# ruff: noqa: RUF001  (regex char classes intentionally include en-dash U+2013 literal)
from __future__ import annotations

import re

from ..models import Citation, Position

# Parenthetical: (Author, YYYY) or (Author et al., YYYY) or (A & B, YYYY)
#   optional ", p. N" / ", pp. N-M"
#   optional "as cited in OtherAuthor, YYYY"
_PAREN_RE = re.compile(
    r"""
    \(
    (?P<authors>[^(),]+?(?:\s*&\s*[^(),]+?)?(?:\s+et\s+al\.)?)
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
    \)
    """,
    re.VERBOSE,
)

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


def parse_citations(text: str) -> list[Citation]:
    cits: list[Citation] = []

    for m in _PAREN_RE.finditer(text):
        if m.group("cited_author") is not None:
            cits.append(
                Citation(
                    raw=m.group(0),
                    authors=[m.group("cited_author").strip()],
                    year=m.group("cited_year"),
                    page=None,
                    narrative=False,
                    secondary_source_author=_split_authors(m.group("authors"))[0],
                    position=Position(start=m.start(), end=m.end()),
                )
            )
        else:
            cits.append(
                Citation(
                    raw=m.group(0),
                    authors=_split_authors(m.group("authors")),
                    year=m.group("year"),
                    page=m.group("page"),
                    narrative=False,
                    position=Position(start=m.start(), end=m.end()),
                )
            )

    for m in _NARRATIVE_RE.finditer(text):
        # Avoid double-counting if the parenthetical regex already matched the same span.
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
