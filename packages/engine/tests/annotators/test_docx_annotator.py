# packages/engine/tests/annotators/test_docx_annotator.py
import io
import zipfile
from pathlib import Path

import pytest
from apa7_validator.annotators.docx import annotate_docx_from_source
from apa7_validator.extractors.docx import DocxExtractor
from apa7_validator.models import Issue, Position, Report, Severity


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_annotated_docx_contains_one_comment_per_issue(sample_docx: bytes):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    # Anchor an issue on the "(Smith, 2020)" citation.
    start = result.text.index("(Smith, 2020)")
    end = start + len("(Smith, 2020)")
    issue = Issue(
        code="citation_without_reference",
        severity=Severity.ERROR,
        message="Test message",
        position=Position(start=start, end=end),
        suggestion="fix it",
        target_kind="citation",
    )
    report = Report(
        references=[],
        citations=[],
        issues=[issue],
        warnings=[],
        degraded_checks=[],
    )
    out = annotate_docx_from_source(
        source_bytes=sample_docx,
        report=report,
        extracted_text=result.text,
        position_map=result.position_map,
    )
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        doc_xml = z.read("word/document.xml").decode()
        assert "commentRangeStart" in doc_xml
        comments_xml = z.read("word/comments.xml").decode()
        assert "Test message" in comments_xml
        assert "fix it" in comments_xml
