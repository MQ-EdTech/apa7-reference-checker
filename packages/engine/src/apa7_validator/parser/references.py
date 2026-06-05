from __future__ import annotations

import re

from apa7_validator.models import Author, Position, Reference, ReferenceType

from .ref_types import try_parse_journal


def parse_references(section: str, body_offset: int) -> list[Reference]:
    """Split a references section into entries and parse each into a `Reference`.

    Entries are separated by blank lines OR by a newline followed by a line
    that starts with a capital letter (heuristic: each new APA reference
    begins with an author surname). For now, blank-line splitting is enough.
    """
    if not section.strip():
        return []

    raw_entries = [chunk.strip() for chunk in re.split(r"\n\s*\n", section) if chunk.strip()]
    refs: list[Reference] = []
    cursor = body_offset
    for entry in raw_entries:
        # Find absolute position within original text.
        start = section.find(entry) + body_offset if section.find(entry) >= 0 else cursor
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
        cursor = start + len(entry)
    return refs


def _try_parse_any(raw: str, position_start: int) -> Reference | None:
    # Order matters: more specific parsers first. Tasks 10-14 extend this.
    for fn in (try_parse_journal,):
        ref = fn(raw, position_start)
        if ref is not None:
            return ref
    return None
