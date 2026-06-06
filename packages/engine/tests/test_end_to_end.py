# packages/engine/tests/test_end_to_end.py
from pathlib import Path

import pytest
from apa7_validator import annotate_docx, validate
from apa7_validator.clients import Clients


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_docx_round_trip_produces_report_and_annotated_docx(sample_docx: bytes):
    report = validate(sample_docx, "docx", clients=Clients.dry_run())
    assert len(report.references) >= 2
    assert len(report.citations) >= 2
    out = annotate_docx(sample_docx, report)
    assert out.startswith(b"PK")


def test_pdf_round_trip(fixture_path: Path):
    pdf_bytes = (fixture_path / "pdf" / "sample_essay.pdf").read_bytes()
    report = validate(pdf_bytes, "pdf", clients=Clients.dry_run())
    assert len(report.references) >= 1
    assert len(report.citations) >= 1


def test_text_with_orphan_citation_is_flagged():
    text = "Climate is warming (Jones, 2099)."
    report = validate(text, "text", clients=Clients.dry_run())
    assert any(i.code == "citation_without_reference" for i in report.issues)
