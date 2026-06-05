"""Common types for all extractors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

PositionKind = Literal["char_offset", "docx_run", "pdf_char_offset"]


@dataclass(frozen=True, slots=True)
class PositionMap:
    """Maps extracted-text offsets back to a source-specific location.

    For now, every extractor uses an identity (char_offset) map. DOCX and PDF
    extractors will extend this with richer maps in Tasks 6 and 7.
    """

    kind: PositionKind

    def to_source(self, extracted_offset: int) -> tuple[PositionKind, int]:
        return (self.kind, extracted_offset)


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
