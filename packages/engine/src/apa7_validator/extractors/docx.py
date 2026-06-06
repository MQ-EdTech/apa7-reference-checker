# packages/engine/src/apa7_validator/extractors/docx.py
from __future__ import annotations

import io
from typing import Any, cast

import docx
from docx.opc.exceptions import PackageNotFoundError

from .base import ExtractionResult, ExtractorError, ParagraphStyle, PositionMap, RunStyle, StyleInfo


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
        paragraph_styles: list[ParagraphStyle] = []
        run_styles: list[RunStyle] = []
        cursor = 0
        for p_idx, para in enumerate(document.paragraphs):
            # Collect paragraph styling metadata.
            fmt = para.paragraph_format
            style_id = (para.style.name if para.style else "") or ""  # type: ignore[union-attr]
            # python-docx exposes these as Length | None; stubs are untyped so we cast.
            hanging = cast("Any", fmt.first_line_indent)  # type: ignore[misc]
            left = cast("Any", fmt.left_indent)  # type: ignore[misc]
            # In python-docx, a hanging indent is represented as a negative
            # first_line_indent with a positive left_indent. The hanging amount
            # equals -first_line_indent when first_line_indent < 0.
            hanging_pt: float | None = None
            if hanging is not None and hanging < 0:
                hanging_pt = float(-hanging.pt)
            left_pt: float | None = None if left is None else float(left.pt)
            paragraph_styles.append(
                ParagraphStyle(
                    paragraph_index=p_idx,
                    style_id=style_id,
                    indent_hanging_pt=hanging_pt,
                    indent_left_pt=left_pt,
                )
            )

            for r_idx, run in enumerate(para.runs):
                # Record run styling for every run (even empty) to keep indexing stable.
                run_styles.append(
                    RunStyle(
                        paragraph_index=p_idx,
                        run_index=r_idx,
                        italic=bool(run.italic),
                        bold=bool(run.bold),
                    )
                )
                # Only add non-empty runs to the position map entries.
                if not run.text:
                    continue
                entries.append((cursor, (p_idx, r_idx, 0)))
                text_parts.append(run.text)
                cursor += len(run.text)
            text_parts.append("\n")
            cursor += 1

        style_info = StyleInfo(paragraphs=paragraph_styles, runs=run_styles)

        return ExtractionResult(
            text="".join(text_parts),
            position_map=PositionMap(kind="docx_run", entries=entries),
            source_kind="docx",
            warnings=[],
            style_info=style_info,
        )
