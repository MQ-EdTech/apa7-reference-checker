# packages/engine/tests/test_api_annotate.py
import io
import zipfile
from pathlib import Path

import pytest
from apa7_validator import annotate_docx, validate
from apa7_validator.clients import Clients


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_annotate_docx_with_source_round_trips(sample_docx: bytes):
    report = validate(sample_docx, "docx", clients=Clients.dry_run())
    out = annotate_docx(sample_docx, report)
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        assert "word/comments.xml" in z.namelist()


def test_annotate_docx_without_source_generates_fresh():
    text = "Body text only. No references heading."
    report = validate(text, "text", clients=Clients.dry_run())
    out = annotate_docx(None, report)
    assert out.startswith(b"PK")  # zip magic
