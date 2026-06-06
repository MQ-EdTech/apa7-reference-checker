from __future__ import annotations

from pathlib import Path

from apa7_validator import validate
from apa7_validator.clients import Clients
from apa7_validator.extractors.base import ParagraphStyle, PositionMap, RunStyle, StyleInfo
from apa7_validator.extractors.docx import DocxExtractor
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.styling import (
    check_book_title_italics,
    check_hanging_indent,
    check_journal_italics,
)

# ---------------------------------------------------------------------------
# Integration tests against sample_essay.docx
# ---------------------------------------------------------------------------


def test_extractor_populates_style_info(fixture_path: Path):
    src = (fixture_path / "docx" / "sample_essay.docx").read_bytes()
    result = DocxExtractor().extract(src)
    assert result.style_info is not None
    # The sample essay has at least one heading + paragraphs.
    assert len(result.style_info.paragraphs) > 0
    assert len(result.style_info.runs) > 0


def test_sample_docx_lacks_hanging_indent(fixture_path: Path):
    """The synthetic sample_essay.docx has no hanging indent on references."""
    src = (fixture_path / "docx" / "sample_essay.docx").read_bytes()
    report = validate(src, "docx", clients=Clients.dry_run())
    assert any(i.code == "hanging_indent_missing" for i in report.issues)


def test_sample_docx_lacks_journal_italics(fixture_path: Path):
    """sample_essay.docx writes the journal name in plain (non-italic) text."""
    src = (fixture_path / "docx" / "sample_essay.docx").read_bytes()
    report = validate(src, "docx", clients=Clients.dry_run())
    assert any(i.code == "journal_italics_missing" for i in report.issues)


def test_text_input_does_not_emit_styling_issues():
    """For text inputs, style_info is None, so styling validators are skipped."""
    text = (
        "Climate is warming (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    report = validate(text, "text", clients=Clients.dry_run())
    styling_codes = {
        "hanging_indent_missing",
        "journal_italics_missing",
        "book_title_italics_missing",
    }
    assert all(i.code not in styling_codes for i in report.issues)


# ---------------------------------------------------------------------------
# Unit tests with constructed StyleInfo (positive cases — no issue when correct)
# ---------------------------------------------------------------------------


def test_hanging_indent_present_emits_no_issue():
    ref = Reference(
        raw="x",
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="x",
        position=Position(0, 1),
    )
    style_info = StyleInfo(
        paragraphs=[
            ParagraphStyle(
                paragraph_index=0,
                style_id="Normal",
                indent_hanging_pt=36.0,
                indent_left_pt=0.0,
            )
        ],
        runs=[],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_hanging_indent([ref], style_info, pm)
    assert issues == []


def test_hanging_indent_missing_emits_warning():
    ref = Reference(
        raw="x",
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="x",
        position=Position(0, 1),
    )
    style_info = StyleInfo(
        paragraphs=[
            ParagraphStyle(
                paragraph_index=0,
                style_id="Normal",
                indent_hanging_pt=None,
                indent_left_pt=None,
            )
        ],
        runs=[],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_hanging_indent([ref], style_info, pm)
    assert any(i.code == "hanging_indent_missing" for i in issues)


def test_journal_italics_present_emits_no_issue():
    # "Climate Journal" starts at offset 0 in the extracted text.
    container = "Climate Journal"
    raw = f"Smith, J. (2020). A study. {container}, 5(2), 100-120."
    ref = Reference(
        raw=raw,
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A study",
        container=container,
        volume="5",
        issue="2",
        pages="100-120",
        position=Position(0, len(raw)),
    )
    style_info = StyleInfo(
        paragraphs=[],
        runs=[
            RunStyle(paragraph_index=0, run_index=0, italic=True, bold=False),
        ],
    )
    # Map position 0 (ref start) -> (para 0, run 0); container offset also lands on run 0.
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_journal_italics([ref], style_info, pm, raw)
    assert issues == []


def test_journal_italics_missing_emits_warning():
    container = "Climate Journal"
    raw = f"Smith, J. (2020). A study. {container}, 5(2), 100-120."
    ref = Reference(
        raw=raw,
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A study",
        container=container,
        volume="5",
        issue="2",
        pages="100-120",
        position=Position(0, len(raw)),
    )
    style_info = StyleInfo(
        paragraphs=[],
        runs=[
            RunStyle(paragraph_index=0, run_index=0, italic=False, bold=False),
        ],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_journal_italics([ref], style_info, pm, raw)
    assert any(i.code == "journal_italics_missing" for i in issues)


def test_book_title_italics_present_emits_no_issue():
    title = "Foundations of Climate Research"
    raw = f"Smith, J. (2020). {title}. Earth Press."
    ref = Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title=title,
        publisher="Earth Press",
        position=Position(0, len(raw)),
    )
    style_info = StyleInfo(
        paragraphs=[],
        runs=[
            RunStyle(paragraph_index=0, run_index=0, italic=True, bold=False),
        ],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_book_title_italics([ref], style_info, pm, raw)
    assert issues == []


def test_book_title_italics_missing_emits_warning():
    title = "Foundations of Climate Research"
    raw = f"Smith, J. (2020). {title}. Earth Press."
    ref = Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title=title,
        publisher="Earth Press",
        position=Position(0, len(raw)),
    )
    style_info = StyleInfo(
        paragraphs=[],
        runs=[
            RunStyle(paragraph_index=0, run_index=0, italic=False, bold=False),
        ],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_book_title_italics([ref], style_info, pm, raw)
    assert any(i.code == "book_title_italics_missing" for i in issues)


def test_book_chapter_container_italics_missing_emits_warning():
    container = "Handbook of Earth Sciences"
    raw = f"Jones, A. (2019). A chapter. In B. Editor (Ed.), {container} (pp. 1-20). Publisher."
    ref = Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK_CHAPTER,
        authors=[Author(family="Jones", given_initials="A.")],
        year="2019",
        title="A chapter",
        container=container,
        pages="1-20",
        publisher="Publisher",
        position=Position(0, len(raw)),
    )
    style_info = StyleInfo(
        paragraphs=[],
        runs=[
            RunStyle(paragraph_index=0, run_index=0, italic=False, bold=False),
        ],
    )
    pm = PositionMap(kind="docx_run", entries=[(0, (0, 0, 0))])
    issues = check_book_title_italics([ref], style_info, pm, raw)
    assert any(i.code == "book_title_italics_missing" for i in issues)
