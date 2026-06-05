from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.cross_cutting import (
    check_alphabetical_order,
    check_doi_format,
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
