from pathlib import Path

import pytest
from apa7_validator.extractors.base import ExtractorError
from apa7_validator.extractors.pdf import PdfExtractor


@pytest.fixture
def sample_pdf(fixture_path: Path) -> bytes:
    return (fixture_path / "pdf" / "sample_essay.pdf").read_bytes()


def test_pdf_extractor_returns_extracted_text(sample_pdf: bytes):
    extractor = PdfExtractor()
    result = extractor.extract(sample_pdf)
    assert "Climate change is well documented" in result.text
    assert result.source_kind == "pdf"


def test_pdf_extractor_position_map_records_page(sample_pdf: bytes):
    extractor = PdfExtractor()
    result = extractor.extract(sample_pdf)
    idx = result.text.index("Climate change")
    kind, ref = result.position_map.to_source(idx)
    assert kind == "pdf_char_offset"
    page_idx, char_offset = ref
    assert page_idx == 0
    assert isinstance(char_offset, int)


def test_pdf_extractor_flags_scanned_pdf_with_no_text():
    # A blank PDF with no text simulates a scanned image.
    import pymupdf

    doc = pymupdf.open()
    doc.new_page()
    blank_bytes = doc.tobytes()
    extractor = PdfExtractor()
    with pytest.raises(ExtractorError) as excinfo:
        extractor.extract(blank_bytes)
    assert excinfo.value.code == "no_extractable_text"
