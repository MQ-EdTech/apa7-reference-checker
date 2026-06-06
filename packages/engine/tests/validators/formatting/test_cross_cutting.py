from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.cross_cutting import (
    check_alphabetical_order,
    check_deprecated_phrases,
    check_doi_format,
    check_reference_count,
    check_title_sentence_case,
    check_year_format,
)


def _ref(
    family: str, year: str = "2020", title: str = "A paper", doi: str | None = None
) -> Reference:
    return Reference(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year=year,
        title=title,
        doi=doi,
        position=Position(0, 1),
    )


def test_alphabetical_order_flags_misordered_pair():
    refs = [_ref("Smith"), _ref("Jones")]
    issues = check_alphabetical_order(refs)
    assert any(i.code == "references_not_alphabetised" for i in issues)


def test_alphabetical_order_clean_when_sorted():
    refs = [_ref("Jones"), _ref("Smith")]
    assert check_alphabetical_order(refs) == []


def test_doi_format_flags_http_prefix_only():
    ref = _ref("Smith", doi="10.1234/abc")
    assert check_doi_format(ref) == []


def test_doi_format_flags_bare_doi_word_prefix():
    ref = _ref("Smith", doi="doi:10.1234/abc")
    issues = check_doi_format(ref)
    assert any(i.code == "doi_malformed" for i in issues)


def test_year_format_accepts_four_digits():
    assert check_year_format(_ref("Smith", year="2020")) == []


def test_year_format_accepts_n_d():
    assert check_year_format(_ref("Smith", year="n.d.")) == []


def test_year_format_rejects_two_digit_year():
    issues = check_year_format(_ref("Smith", year="20"))
    assert any(i.code == "year_malformed" for i in issues)


def test_title_sentence_case_flags_title_case():
    issues = check_title_sentence_case(_ref("Smith", title="A Paper About Things"))
    assert any(i.code == "title_not_sentence_case" for i in issues)


def test_title_sentence_case_accepts_sentence_case():
    assert check_title_sentence_case(_ref("Smith", title="A paper about things")) == []


def test_deprecated_doi_prefix_emits_warning():
    ref = Reference(
        raw="Smith, J. (2020). A paper. Journal, 5(2), 100-120. doi:10.1234/abc",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        doi="10.1234/abc",
        position=Position(0, 100),
    )
    issues = check_doi_format(ref)
    assert any(i.code == "doi_surface_form_deprecated" for i in issues)


def test_canonical_doi_url_does_not_emit_deprecation_warning():
    ref = Reference(
        raw="Smith, J. (2020). A paper. Journal, 5(2). https://doi.org/10.1234/abc",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        doi="10.1234/abc",
        position=Position(0, 100),
    )
    issues = check_doi_format(ref)
    assert all(i.code != "doi_surface_form_deprecated" for i in issues)


def test_reference_count_below_minimum_emits_warning():
    refs = [_ref(f"Author{i}") for i in range(5)]
    issues = check_reference_count(refs)
    assert any(i.code == "reference_count_below_minimum" for i in issues)


def test_reference_count_at_minimum_clean():
    refs = [_ref(f"Author{i}") for i in range(10)]
    assert check_reference_count(refs) == []


def test_deprecated_retrieved_from_warning():
    ref = Reference(
        raw="Smith, J. (2020). A page. Retrieved from https://example.com",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A page",
        position=Position(0, 60),
    )
    issues = check_deprecated_phrases(ref)
    assert any(i.code == "deprecated_retrieved_from" for i in issues)


def test_deprecated_accessed_date_warning():
    ref = Reference(
        raw="Smith, J. (2020). A page. Accessed: 1 January 2021.",
        ref_type=ReferenceType.WEBSITE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A page",
        position=Position(0, 50),
    )
    issues = check_deprecated_phrases(ref)
    assert any(i.code == "deprecated_accessed_date" for i in issues)


def test_clean_reference_no_deprecated_phrases():
    ref = Reference(
        raw="Smith, J. (2020). A page. https://example.com",
        ref_type=ReferenceType.WEBSITE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A page",
        position=Position(0, 40),
    )
    assert check_deprecated_phrases(ref) == []
