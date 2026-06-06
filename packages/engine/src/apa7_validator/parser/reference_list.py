from __future__ import annotations

import re

_HEADING_RE = re.compile(
    r"^[ \t]*"
    r"(?:\d+(?:\.\d+)*[.\s]+)?"  # optional numeric prefix: "5.0 " / "5. " / "5.1 " / "1. "
    r"(references|reference list|bibliography|works cited)"
    r"[ \t]*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def split_body_and_references(text: str) -> tuple[str, str, bool]:
    """Return (body, references_section, found).

    Splits on the first line that is purely a recognised heading. If no heading
    is found, returns the full text as the body and an empty references section.
    """
    match = _HEADING_RE.search(text)
    if not match:
        return text, "", False
    body = text[: match.start()].rstrip()
    refs = text[match.end() :].lstrip("\n")
    return body, refs, True
