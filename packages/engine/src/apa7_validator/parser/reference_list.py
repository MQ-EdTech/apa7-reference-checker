from __future__ import annotations

import re

from .references import looks_like_new_ref as _looks_like_new_ref

_HEADING_RE = re.compile(
    r"""
    ^[ \t]*
    (?:
        \d+(?:\.\d+)*[.\s]+         # numeric prefix: "5." "5.0 " "5.1 "
      | [IVXLCDM]+\.\s+              # uppercase Roman numerals: "V. " "IV. "
      | [ivxlcdm]+\.\s+              # lowercase Roman numerals: "v. " "iv. "
    )?
    (references?|reference\s+list|bibliography|works\s+cited)
    [ \t]*:?[ \t]*$
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
)


def _find_references_block_heuristically(text: str) -> tuple[str, str] | None:
    """If no References heading is present, try to detect the references block.

    Walks lines from the end of the document; if we find at least 3 lines that
    look like reference starts within the last 30% of the document, we treat
    the position of the first such line as the start of the references section.
    """
    lines = text.split("\n")
    if not lines:
        return None

    # Build a list of (char_offset_in_text, line_text) for non-empty lines.
    offsets: list[tuple[int, str]] = []
    cursor = 0
    for raw in lines:
        if raw.strip():
            offsets.append((cursor, raw))
        cursor += len(raw) + 1  # +1 for the newline removed by split

    if not offsets:
        return None

    # Last 30% of text by character offset.
    cutoff = int(len(text) * 0.70)

    # Walk forward: find all indices in offsets where the line looks like a
    # reference start.
    start_indices: list[int] = []
    for i, (_off, line) in enumerate(offsets):
        if _looks_like_new_ref(line):
            start_indices.append(i)

    if len(start_indices) < 3:
        return None

    # The earliest of the consecutive run that's still in the last 30%.
    # We accept the heuristic if at least 3 reference-start lines exist after
    # the cutoff, and the first such line is past the cutoff.
    qualifying = [i for i in start_indices if offsets[i][0] >= cutoff]
    if len(qualifying) < 3:
        return None
    first_qualifying_offset = offsets[qualifying[0]][0]
    refs_section = text[first_qualifying_offset:]
    body = text[:first_qualifying_offset].rstrip()
    return body, refs_section


def split_body_and_references(text: str) -> tuple[str, str, bool]:
    """Return (body, references_section, found).

    Splits on the first line that is purely a recognised heading. If no heading
    is found, falls back to a heuristic that scans the last ~30% of the text
    for a contiguous block of lines that all look like reference starts.
    """
    # Normalise non-breaking spaces to regular spaces (common DOCX artifact).
    normalised = text.replace("\xa0", " ")

    match = _HEADING_RE.search(normalised)
    if match:
        body = normalised[: match.start()].rstrip()
        refs = normalised[match.end() :].lstrip("\n")
        return body, refs, True

    # Heuristic fallback.
    heuristic = _find_references_block_heuristically(normalised)
    if heuristic is not None:
        body, refs = heuristic
        return body, refs, True

    return text, "", False
