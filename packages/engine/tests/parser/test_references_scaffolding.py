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


def test_unknown_reference_still_captures_author_and_year_for_cross_matching():
    # Real student bibliography: missing period after (2023) and trailing
    # publisher chain breaks the strict journal/book parsers, so this falls
    # through to UNKNOWN. The fallback extractor must still recover the
    # leading author surname and the year so the cross-matcher can link
    # citations like "(Elliott et al., 2023)" to this reference.
    section = (
        "Elliott, G., Rundle-Thiele, S., Waller, D., Bentrott, I. (2023) "
        "Marketing, (6th ed.). John Wiley & Sons, Incorporated. ProQuest."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].ref_type is ReferenceType.UNKNOWN
    assert refs[0].authors[0].family == "Elliott"
    assert refs[0].year == "2023"


def test_unknown_reference_with_et_al_form_captures_first_author():
    # "Sozuer et al. (2020). Title. A Journal of X. Springer Nature." falls
    # through all parsers (no volume, trailing publisher chain). Fallback
    # should still extract Sozuer-as-author + 2020.
    section = (
        "Sozuer et al. (2020). The Past, Present, and Future of Marketing Strategy. "
        "A Journal of Research in Marketing. Springer Nature."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    # Fallback keeps "Sozuer et al." as the family stub; cross_matching's
    # _normalise_family strips the "et al." before comparing keys.
    assert "Sozuer" in refs[0].authors[0].family
    assert refs[0].year == "2020"


def test_unknown_reference_with_multi_word_org_name_keeps_full_name():
    # "Lululemon Athletica. (2025). 2024 Impact Report. Lululemon." actually
    # matches the report parser (the word "Report" triggers the hint regex)
    # but the family is kept with its trailing period — cross_matching's
    # _normalise_family strips trailing punctuation before comparing.
    section = "Lululemon Athletica. (2025). 2024 Impact Report. Lululemon."
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    # Family may end with "." per parser convention — strip for the check.
    assert refs[0].authors[0].family.rstrip(".") == "Lululemon Athletica"
    assert refs[0].year == "2025"


def test_unknown_reference_with_single_word_org_keeps_org():
    section = "ThisRock. (2025). Lululemon Sustainability Report. ThisRock ESG."
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].authors[0].family.rstrip(".") == "ThisRock"
    assert refs[0].year == "2025"


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


def test_splits_bullet_pointed_references():
    section = (
        "• Smith, J. (2020). Foundations of climate research. Earth Press.\n"
        "• Jones, A., & Lee, B. (2021). New analyses. Climate Journal, 5(2)."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2
    assert refs[0].authors[0].family == "Smith"
    assert refs[1].authors[0].family == "Jones"


def test_splits_dash_bulleted_references():
    section = (
        "- Smith, J. (2020). Foundations. Earth Press.\n"
        "- Jones, A. (2021). New analyses. Journal of Things, 5(2)."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_splits_numbered_references():
    section = (
        "1. Smith, J. (2020). Foundations. Earth Press.\n"
        "2. Jones, A. (2021). New analyses. Journal of Things, 5(2)."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_splits_parenthesised_numbered_references():
    section = (
        "(1) Smith, J. (2020). Foundations. Earth Press.\n"
        "(2) Jones, A. (2021). New analyses. Journal of Things, 5(2)."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2
