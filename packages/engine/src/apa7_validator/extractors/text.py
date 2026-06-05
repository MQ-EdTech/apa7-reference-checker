from __future__ import annotations

from .base import ExtractionResult, PositionMap


class TextExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, bytes):
            text = source.decode("utf-8")
        else:
            text = source
        return ExtractionResult(
            text=text,
            position_map=PositionMap(kind="char_offset"),
            source_kind="text",
            warnings=[],
        )
