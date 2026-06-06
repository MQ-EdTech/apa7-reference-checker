from __future__ import annotations

import io
from typing import Any

from .base import ExtractionResult, ExtractorError, PositionMap


class PdfExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, str):
            raise ExtractorError(
                "invalid_input",
                "PdfExtractor requires bytes, got str",
            )
        try:
            # pymupdf is an optional native dependency (see pyproject.toml
            # `[project.optional-dependencies] native`). It's a C extension and
            # not installable under Pyodide, so we import it lazily — the
            # module loads fine without it; only extract() requires it.
            import pymupdf
        except ImportError as exc:
            raise ExtractorError(
                "pdf_extractor_unavailable",
                "PDF extraction requires the 'native' extra (install via "
                "`uv sync --extra native` or `pip install apa7-validator[native]`).",
            ) from exc
        try:
            doc = pymupdf.open(stream=io.BytesIO(source), filetype="pdf")
        except Exception as exc:
            raise ExtractorError("invalid_pdf", str(exc)) from exc

        if doc.needs_pass:  # type: ignore[union-attr]
            raise ExtractorError("encrypted_input", "PDF is password-protected")

        text_parts: list[str] = []
        entries: list[tuple[int, Any]] = []
        cursor = 0
        page_count: int = len(doc)  # type: ignore[arg-type]
        for page_idx in range(page_count):
            page = doc[page_idx]  # type: ignore[index]
            page_text: str = page.get_text("text")  # type: ignore[union-attr]
            if page_text:
                entries.append((cursor, (page_idx, 0)))
                text_parts.append(page_text)
                cursor += len(page_text)
            if page_idx < page_count - 1:
                text_parts.append("\n")
                cursor += 1

        full_text = "".join(text_parts)
        if not full_text.strip():
            raise ExtractorError(
                "no_extractable_text",
                "PDF has no extractable text (likely scanned); OCR required",
            )

        return ExtractionResult(
            text=full_text,
            position_map=PositionMap(kind="pdf_char_offset", entries=entries),
            source_kind="pdf",
            warnings=[],
        )
