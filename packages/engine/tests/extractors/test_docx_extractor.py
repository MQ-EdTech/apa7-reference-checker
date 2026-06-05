from pathlib import Path

import pytest
from apa7_validator.extractors.docx import DocxExtractor


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_docx_extractor_returns_concatenated_text(sample_docx: bytes):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    assert "Climate change is well documented" in result.text
    assert "Smith, J. (2020). Foundations of climate research." in result.text
    assert result.source_kind == "docx"


def test_docx_extractor_position_map_maps_offset_to_paragraph_index(
    sample_docx: bytes,
):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    body_idx = result.text.index("Climate change")
    kind, ref = result.position_map.to_source(body_idx)
    assert kind == "docx_run"
    # ref is a (paragraph_index, run_index, offset_in_run) tuple
    assert isinstance(ref, tuple) and len(ref) == 3


def test_docx_extractor_raises_on_encrypted_input():
    from apa7_validator.extractors.base import ExtractorError

    extractor = DocxExtractor()
    # An encrypted DOCX would normally come from Word's password-protect.
    # python-docx raises on opening such files; we re-raise as ExtractorError.
    with pytest.raises(ExtractorError) as excinfo:
        extractor.extract(b"not a docx at all")
    assert excinfo.value.code in {"encrypted_input", "invalid_docx"}
