from __future__ import annotations

import re

from ...models import Position, Reference, ReferenceType
from .journal import parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^[]+?)\s*
    \[(?P<model_kind>[^\]]+)\]\.\s*
    (?P<url>https?://\S+)\s*$
    """,
    re.VERBOSE,
)

_MODEL_KIND_HINT = re.compile(
    r"large language model|generative ai|ai model|gpt|llm",
    re.IGNORECASE,
)


def try_parse_ai_source(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    if not _MODEL_KIND_HINT.search(m.group("model_kind")):
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.AI_SOURCE,
        authors=parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        url=m.group("url"),
        extras={"model_kind": m.group("model_kind").strip()},
        position=Position(start=position_start, end=position_start + len(raw)),
    )
