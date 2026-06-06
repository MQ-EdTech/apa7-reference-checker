from apa7_validator.parser.reference_list import split_body_and_references


def test_splits_on_standard_references_heading():
    text = "Body text here.\n\nReferences\n\nSmith, J. (2020). A paper. Journal."
    body, refs_section, found = split_body_and_references(text)
    assert "Body text here." in body
    assert "Smith, J. (2020)" in refs_section
    assert found is True


def test_splits_on_bibliography_heading():
    text = "Body.\n\nBibliography\n\nSmith, J. (2020)."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_returns_full_text_when_no_heading_found():
    text = "Body only, no references heading."
    body, refs, found = split_body_and_references(text)
    assert body == text
    assert refs == ""
    assert found is False


def test_heading_match_is_case_insensitive_and_line_anchored():
    text = "Body mentions references casually.\n\nREFERENCES\n\nSmith, J."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs
