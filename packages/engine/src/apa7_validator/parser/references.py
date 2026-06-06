from __future__ import annotations

import re

from ..models import Author, Position, Reference, ReferenceType
from .ref_types import (
    try_parse_ai_source,
    try_parse_book,
    try_parse_book_chapter,
    try_parse_journal,
    try_parse_report,
    try_parse_website,
)

# A line looks like the START of a new reference when it begins with:
#   - "Lastname, F." or "Lastname, F. M." (personal name + initials)
#   - "Lastname et al." (Latin abbreviation)
#   - "Capitalized Word [Word ...]." followed by "(YYYY)" (org name + year)
_NEW_REF_RE = re.compile(
    r"""
    ^(?:
        # Personal name pattern: "Smith, J." or "Smith-Jones, J. K." etc.
        [A-Z][a-zA-Z\-']+,\s+[A-Z]\.
      |
        # "et al." form: "Smith et al."
        [A-Z][a-zA-Z\-']+\s+et\s+al\.
      |
        # Organisation form: "Capital [Word ...] . (YYYY)"
        [A-Z][\w'\-]+(?:\s+[A-Z][\w'\-]+)*\.\s+\(\d{4}
    )
    """,
    re.VERBOSE,
)


_LIST_MARKER_RE = re.compile(
    r"""
    ^[\s\t]*
    (?:
        [•‣◦∙●■□]   # bullet glyphs
      | [\-*+]                                                  # ASCII bullets
      | \d+[\.\)]                                                # 1. or 1)
      | \(\d+\)                                                  # (1)
      | [a-zA-Z][\.\)]                                           # a. or a)
    )
    \s+
    """,
    re.VERBOSE,
)


def _strip_list_marker(line: str) -> str:
    return _LIST_MARKER_RE.sub("", line, count=1).strip()


def _looks_like_new_ref(line: str) -> bool:
    stripped = _strip_list_marker(line)
    return bool(_NEW_REF_RE.match(stripped))


# Fallback extractor: when no specific ref-type parser matches, pull the
# author-family stub and the year from the raw text so cross-matching can
# still link the UNKNOWN ref to its citations.
#
# Captures everything up to the first "(YYYY)" marker, then post-processes:
#   - Person-list shape ("Lastname, F.[, more]")  -> keep just the first surname
#   - Org / "et al." shape                         -> keep the whole pre-paren block
_FALLBACK_RE = re.compile(
    r"""
    ^\s*(?P<authors_raw>[^(]+?)
    \s*\((?P<year>\d{4}[a-z]?)\)
    """,
    re.VERBOSE,
)

_PERSON_LIST_RE = re.compile(r"^[A-Z][a-zA-Z\-']+,\s+[A-Z]\.")
_FIRST_SURNAME_RE = re.compile(r"^([A-Z][a-zA-Z\-']+)")


def _fallback_author_year(raw: str) -> tuple[str, str] | None:
    m = _FALLBACK_RE.match(raw)
    if not m:
        return None
    authors_raw = m.group("authors_raw").rstrip(".").strip()
    year = m.group("year")
    if _PERSON_LIST_RE.match(authors_raw):
        # Person list: take just the first surname.
        first = _FIRST_SURNAME_RE.match(authors_raw)
        if first:
            return (first.group(1), year)
    # Org name or "et al." form: keep the whole pre-paren block;
    # cross_matching's _normalise_family will strip "et al." for us.
    return (authors_raw, year)


def _prev_continues_author_list(prev: str) -> bool:
    """Author lists wrap with a trailing comma or ampersand on the previous line."""
    stripped = prev.rstrip()
    return stripped.endswith((",", "&"))


def _split_into_entries(section: str) -> list[str]:
    lines = [line.strip() for line in section.split("\n") if line.strip()]
    entries: list[str] = []
    current: list[str] = []
    for line in lines:
        prev = current[-1] if current else ""
        line_starts_ref = _looks_like_new_ref(line)
        if line_starts_ref and not _prev_continues_author_list(prev):
            if current:
                entries.append(" ".join(current).strip())
            current = [_strip_list_marker(line)]
        else:
            current.append(line)
    if current:
        entries.append(" ".join(current).strip())
    return entries


def parse_references(section: str, body_offset: int) -> list[Reference]:
    """Split a references section into entries and parse each into a `Reference`.

    Handles wrapped lines (each visible line in the DOCX becomes a separate
    ``\\n``-separated text line) by detecting which lines begin a new entry and
    joining continuation lines with a single space.
    """
    if not section.strip():
        return []
    entries = _split_into_entries(section)
    refs: list[Reference] = []
    search_from = 0
    for entry in entries:
        local = (
            section.find(entry[:60], search_from)
            if len(entry) >= 60
            else section.find(entry, search_from)
        )
        # If the joined entry doesn't appear verbatim in the section (because we
        # collapsed newlines into spaces), fall back to search_from.
        start = (local + body_offset) if local >= 0 else (search_from + body_offset)
        parsed = _try_parse_any(entry, start)
        if parsed is None:
            fallback = _fallback_author_year(entry)
            family, year = fallback if fallback else ("?", "")
            parsed = Reference(
                raw=entry,
                ref_type=ReferenceType.UNKNOWN,
                authors=[Author(family=family, given_initials="")],
                year=year,
                title="",
                position=Position(start=start, end=start + len(entry)),
            )
        refs.append(parsed)
        search_from = (local + len(entry)) if local >= 0 else (search_from + len(entry))
    return refs


def _try_parse_any(raw: str, position_start: int) -> Reference | None:
    for fn in (
        try_parse_ai_source,
        try_parse_journal,
        try_parse_book_chapter,
        try_parse_website,
        try_parse_report,
        try_parse_book,
    ):
        ref = fn(raw, position_start)
        if ref is not None:
            return ref
    return None
