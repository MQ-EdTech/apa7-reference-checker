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


def test_splits_wrapped_personal_name_reference():
    section = (
        "Chen, Y., et al. (2021). The Role of Corporate Social Responsibility and Corporate\n"
        "Image in Times of Crisis. Journal of Things, 18(16), 8275."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].authors[0].family == "Chen"


def test_splits_wrapped_multi_author_list():
    # Author list wraps across two lines, ending with ", " on the wrap point.
    section = (
        "Elliott, G., Rundle-Thiele, S., Waller, D., Bentrott, I., Hatton-Jones, S., Jeans, P.,\n"
        "Joshua Anandappa, S., & Campbell, P. (2023). Marketing. John Wiley & Sons.\n\n"
        "Smith, J. (2020). Foundations. Earth Press."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2
    assert refs[0].authors[0].family == "Elliott"
    assert refs[1].authors[0].family == "Smith"


def test_splits_org_name_reference():
    section = (
        "Lululemon Athletica. (2025). 2024 Impact Report. Lululemon.\n\n"
        "Smith, J. (2020). Foundations. Earth Press."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_splits_et_al_form_org_reference():
    section = (
        "Sozuer et al. (2020). The Past, Present, and Future of Marketing Strategy.\n"
        "A Journal of Research in Marketing. Springer Nature.\n\n"
        "Smith, J. (2020). Foundations. Earth Press."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_mixed_personal_and_org_references():
    section = (
        "Chen, Y. (2021). Title. Journal of Things.\n"
        "Lululemon Athletica. (2025). 2024 Impact Report. Lululemon.\n"
        "ThisRock. (2025). Lululemon Sustainability Report. ThisRock ESG.\n"
        "Wolfe, I. (2024). How Ethical is Lululemon. Good On You."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 4
