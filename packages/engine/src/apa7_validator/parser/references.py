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


def parse_references(section: str, body_offset: int) -> list[Reference]:
    """Split a references section into entries and parse each into a `Reference`.

    Entries are separated by blank lines OR by a newline followed by a line
    that starts with a capital letter (heuristic: each new APA reference
    begins with an author surname, e.g. "Smith, J." or "Jones, A., & Lee").
    This handles both double-newline (text/PDF) and single-newline (DOCX)
    paragraph separators.
    """
    if not section.strip():
        return []

    # First normalise: replace a newline that is immediately followed by an
    # uppercase letter + comma/period/space (APA author pattern) with a double
    # newline so the existing blank-line splitter can do the rest.
    normalised = re.sub(r"\n(?=[A-Z][a-zA-Z'\-]+(,| [A-Z]\.))", "\n\n", section)
    raw_entries = [chunk.strip() for chunk in re.split(r"\n\s*\n", normalised) if chunk.strip()]
    refs: list[Reference] = []
    search_from = 0  # track where the next find should start
    for entry in raw_entries:
        # Find absolute position within original text.
        local = section.find(entry, search_from)
        if local < 0:
            # Fallback — shouldn't normally happen
            local = search_from
        start = local + body_offset
        parsed = _try_parse_any(entry, start)
        if parsed is None:
            parsed = Reference(
                raw=entry,
                ref_type=ReferenceType.UNKNOWN,
                authors=[Author(family="?", given_initials="")],
                year="",
                title="",
                position=Position(start=start, end=start + len(entry)),
            )
        refs.append(parsed)
        search_from = local + len(entry)
    return refs


def _try_parse_any(raw: str, position_start: int) -> Reference | None:
    # Order matters: more specific parsers first. Tasks 11-14 extend this.
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
