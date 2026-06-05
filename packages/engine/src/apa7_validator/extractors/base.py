# packages/engine/src/apa7_validator/extractors/base.py
"""Common types for all extractors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

PositionKind = Literal["char_offset", "docx_run", "pdf_char_offset"]


@dataclass(frozen=True, slots=True)
class PositionMap:
    """Maps extracted-text offsets back to a source-specific location.

    `entries` is a sorted list of (extracted_offset, source_ref) tuples. For
    `kind="char_offset"` the entries list is empty (identity). For `kind="docx_run"`
    each entry's source_ref is (paragraph_index, run_index, offset_in_run). For
    `kind="pdf_char_offset"` each entry's source_ref is (page_index, char_offset).
    """

    kind: PositionKind
    entries: list[tuple[int, Any]] = field(default_factory=lambda: [])

    def to_source(self, extracted_offset: int) -> tuple[PositionKind, Any]:
        if self.kind == "char_offset":
            return ("char_offset", extracted_offset)
        # Find the last entry whose offset <= extracted_offset.
        lo, hi = 0, len(self.entries) - 1
        best = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.entries[mid][0] <= extracted_offset:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return (self.kind, self.entries[best][1])


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    position_map: PositionMap
    source_kind: Literal["text", "docx", "pdf"]
    warnings: list[str]


class Extractor(Protocol):
    def extract(self, source: bytes | str) -> ExtractionResult: ...


class ExtractorError(Exception):
    """Base for extractor-level failures (encrypted input, no extractable text)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
