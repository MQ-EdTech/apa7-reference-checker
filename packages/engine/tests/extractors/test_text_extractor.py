from apa7_validator.extractors.text import TextExtractor


def test_text_extractor_returns_extraction_result():
    extractor = TextExtractor()
    result = extractor.extract("Hello world.")
    assert result.text == "Hello world."
    assert result.position_map.kind == "char_offset"
    assert result.source_kind == "text"


def test_text_extractor_preserves_offsets_via_identity_map():
    extractor = TextExtractor()
    result = extractor.extract("ABCDE")
    # For text input, source offset == extracted offset (identity map)
    assert result.position_map.to_source(2) == ("char_offset", 2)
