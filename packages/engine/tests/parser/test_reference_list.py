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


def test_splits_on_numbered_heading():
    text = "Body.\n\n5.0 References\n\nSmith, J. (2020)."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_splits_on_decimal_subsection_heading():
    text = "Body.\n\n5.1 References\n\nSmith, J. (2020)."
    _body, _refs, found = split_body_and_references(text)
    assert found is True


def test_does_not_match_toc_entry_with_trailing_dots():
    # Table-of-contents-style line: "References" followed by leader dots.
    text = "References ............................................\nBody...\n\nReferences\n\nSmith, J. (2020)."
    _body, refs, found = split_body_and_references(text)
    # The first "References ......." should NOT be treated as the section heading.
    # The bare "References" on the third-from-end line SHOULD be.
    assert found is True
    assert "Smith" in refs


def test_handles_non_breaking_space_in_heading():
    text = "Body.\n\n5. References\xa0\n\nSmith, J. (2020). Title. Journal."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_handles_singular_reference_heading():
    text = "Body.\n\nReference \n\nSmith, J. (2020). Title. Journal."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_handles_roman_numeral_prefix_uppercase():
    text = "Body.\n\nV. References\n\nSmith, J. (2020). Title. Journal."
    _body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_handles_roman_numeral_prefix_lowercase():
    text = "Body.\n\niv. References\n\nSmith, J. (2020). Title. Journal."
    _body, _refs, found = split_body_and_references(text)
    assert found is True


def test_heuristic_fallback_when_no_heading():
    # No heading at all; references just appear at the end. Three ref-start
    # lines should be enough to trigger the heuristic.
    body_filler = "Body paragraph.\n" * 30
    refs = (
        "Smith, J. (2020). Title. Journal of Things, 5(2), 100-120.\n"
        "Jones, A. (2021). Another paper. Climate Journal, 8(4), 200-225.\n"
        "Brown, K. (2018). Statistical methods. Academic Press."
    )
    text = body_filler + "\n" + refs
    _body, refs_out, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs_out
    assert "Jones" in refs_out
    assert "Brown" in refs_out


def test_heuristic_fallback_does_not_trigger_on_too_few_refs():
    # Only 1 reference-shaped line at the end — not enough for the heuristic.
    text = "Body filler. " * 50 + "\nSmith, J. (2020). Title. Earth Press."
    _body, _refs, found = split_body_and_references(text)
    assert found is False
