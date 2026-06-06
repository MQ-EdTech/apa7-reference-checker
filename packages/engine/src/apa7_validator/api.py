"""Public API of the validator engine.

The actual implementations are wired in Task 37 (validate) and Task 38
(annotate_docx). This module defines the stable surface area.
"""

from __future__ import annotations

import asyncio
from typing import Literal

from .annotators.docx import annotate_docx_from_source, annotate_docx_from_text
from .clients.base import Clients
from .extractors import DocxExtractor, PdfExtractor, TextExtractor
from .extractors.base import ExtractionResult
from .models import Issue, Report
from .parser import parse_citations, parse_references, split_body_and_references
from .reporter import assemble
from .validators import IssueBuilder
from .validators.cross_matching import check_cross_matching
from .validators.existence import check_existence
from .validators.formatting.ai_source import check_ai_source
from .validators.formatting.book import check_book
from .validators.formatting.book_chapter import check_book_chapter
from .validators.formatting.cross_cutting import (
    check_alphabetical_order,
    check_deprecated_phrases,
    check_doi_format,
    check_reference_count,
    check_title_sentence_case,
    check_year_format,
)
from .validators.formatting.journal import check_journal
from .validators.formatting.report import check_report
from .validators.formatting.styling import (
    check_book_title_italics,
    check_hanging_indent,
    check_journal_italics,
)
from .validators.formatting.website import check_website

__all__ = ["Format", "IssueBuilder", "annotate_docx", "validate", "validate_async"]

Format = Literal["text", "docx", "pdf"]


def _extract(source: bytes | str, format: Format) -> ExtractionResult:
    if format == "text":
        return TextExtractor().extract(source)
    if format == "docx":
        if isinstance(source, str):
            raise TypeError("DOCX validation requires bytes, got str")
        return DocxExtractor().extract(source)
    if format == "pdf":
        if isinstance(source, str):
            raise TypeError("PDF validation requires bytes, got str")
        return PdfExtractor().extract(source)
    raise ValueError(f"unknown format: {format!r}")


async def validate_async(
    source: bytes | str,
    format: Format,
    *,
    clients: Clients | None = None,
) -> Report:
    if clients is None:
        clients = Clients.dry_run()
    extracted = _extract(source, format)
    body, refs_section, found = split_body_and_references(extracted.text)
    references = parse_references(refs_section, body_offset=len(body))
    citations = parse_citations(body)

    formatting_issues: list[Issue] = []
    formatting_issues += check_alphabetical_order(references)
    formatting_issues += check_reference_count(references)
    for ref in references:
        formatting_issues += check_doi_format(ref)
        formatting_issues += check_year_format(ref)
        formatting_issues += check_title_sentence_case(ref)
        formatting_issues += check_deprecated_phrases(ref)
        formatting_issues += check_journal(ref)
        formatting_issues += check_book(ref)
        formatting_issues += check_book_chapter(ref)
        formatting_issues += check_website(ref)
        formatting_issues += check_report(ref)
        formatting_issues += check_ai_source(ref)

    if extracted.style_info is not None:
        formatting_issues += check_hanging_indent(
            references,
            extracted.style_info,
            extracted.position_map,
        )
        formatting_issues += check_journal_italics(
            references,
            extracted.style_info,
            extracted.position_map,
            extracted.text,
        )
        formatting_issues += check_book_title_italics(
            references,
            extracted.style_info,
            extracted.position_map,
            extracted.text,
        )

    cross_issues = check_cross_matching(citations, references)
    existence_issues, degraded = await check_existence(references, clients)

    warnings = [] if found else ["no_reference_list_found"]

    return assemble(
        references=references,
        citations=citations,
        formatting_issues=formatting_issues,
        cross_matching_issues=cross_issues,
        existence_issues=existence_issues,
        warnings=warnings,
        degraded_checks=degraded,
    )


def validate(
    source: bytes | str,
    format: Format,
    *,
    clients: Clients | None = None,
) -> Report:
    return asyncio.run(validate_async(source, format, clients=clients))


def annotate_docx(source: bytes | None, report: Report) -> bytes:
    if source is None:
        # Reconstruct flat text from the report's references and citations.
        # For text-only inputs we don't have the original; the SPA is expected
        # to call annotate_docx_from_text with the raw text directly when it has it.
        # Here we use the raw form available on Reference.raw / Citation.raw.
        parts: list[str] = []
        for c in report.citations:
            parts.append(c.raw)
        if report.references:
            parts.append("\n\nReferences\n")
            for r in report.references:
                parts.append(r.raw)
        text = "\n".join(parts) or " "
        return annotate_docx_from_text(text=text, report=report)
    # Re-extract to get position_map.
    extracted = DocxExtractor().extract(source)
    return annotate_docx_from_source(
        source_bytes=source,
        report=report,
        extracted_text=extracted.text,
        position_map=extracted.position_map,
    )
