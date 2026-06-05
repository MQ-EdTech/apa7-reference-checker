import io
import zipfile

from apa7_validator.annotators.docx import annotate_docx_from_text
from apa7_validator.models import Issue, Position, Report, Severity


def test_fresh_docx_carries_text_and_comments():
    text = "Climate change is well documented (Smith, 2020).\n"
    issue = Issue(
        code="x",
        severity=Severity.ERROR,
        message="m",
        position=Position(text.index("(Smith"), text.index(")") + 1),
        suggestion="fix",
    )
    report = Report(
        references=[],
        citations=[],
        issues=[issue],
        warnings=[],
        degraded_checks=[],
    )
    out = annotate_docx_from_text(text=text, report=report)
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        doc_xml = z.read("word/document.xml").decode()
        assert "Climate change" in doc_xml
        assert "commentRangeStart" in doc_xml
        comments_xml = z.read("word/comments.xml").decode()
        assert "fix" in comments_xml
