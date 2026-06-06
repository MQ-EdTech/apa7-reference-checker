from apa7_validator.models import ReferenceType
from apa7_validator.parser.references import parse_references


def test_returns_empty_list_for_empty_section():
    refs = parse_references("", body_offset=0)
    assert refs == []


def test_splits_on_blank_lines_between_entries():
    section = (
        "Smith, J. (2020). A paper. Journal of Things, 1(2), 3-4.\n\n"
        "Jones, A. (2021). Another paper. Journal of Things, 2(3), 4-5."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_unparseable_entry_returned_with_unknown_type():
    section = "This is not a reference at all."
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].ref_type is ReferenceType.UNKNOWN


def test_duplicate_entries_get_distinct_positions():
    entry = "Smith, J. (2020). A paper. Journal of Things, 5(2), 100-120."
    section = entry + "\n\n" + entry
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2
    # Positions must be distinct — second entry starts after first ends.
    assert refs[0].position.start < refs[1].position.start
    assert refs[1].position.start >= refs[0].position.end


def test_smith_foundations_book_is_classified_as_book():
    section = "Smith, J. (2020). Foundations of climate research. Earth Press."
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].ref_type is ReferenceType.BOOK
    assert refs[0].publisher == "Earth Press"
