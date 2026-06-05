# packages/engine/src/apa7_validator/extractors/docx.py
from __future__ import annotations

import io
from typing import Any

import docx
from docx.opc.exceptions import PackageNotFoundError

from .base import ExtractionResult, ExtractorError, PositionMap


class DocxExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, str):
            raise ExtractorError(
                "invalid_input",
                "DocxExtractor requires bytes, got str",
            )
        try:
            document = docx.Document(io.BytesIO(source))
        except PackageNotFoundError as exc:
            raise ExtractorError(
                "invalid_docx",
                f"Not a valid DOCX file: {exc}",
            ) from exc
        except Exception as exc:
            if "encrypted" in str(exc).lower() or "password" in str(exc).lower():
                raise ExtractorError(
                    "encrypted_input",
                    "DOCX is password-protected",
                ) from exc
            raise ExtractorError("invalid_docx", str(exc)) from exc

        text_parts: list[str] = []
        entries: list[tuple[int, Any]] = []
        cursor = 0
        for p_idx, para in enumerate(document.paragraphs):
            for r_idx, run in enumerate(para.runs):
                if not run.text:
                    continue
                entries.append((cursor, (p_idx, r_idx, 0)))
                text_parts.append(run.text)
                cursor += len(run.text)
            text_parts.append("\n")
            cursor += 1

        return ExtractionResult(
            text="".join(text_parts),
            position_map=PositionMap(kind="docx_run", entries=entries),
            source_kind="docx",
            warnings=[],
        )
