from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.journal import try_parse_journal


def test_parses_basic_journal_reference():
    raw = (
        "Smith, J. K. (2020). The effects of A on B. "
        "Journal of Things, 5(2), 100-120. https://doi.org/10.1234/jot.2020.05"
    )
    ref = try_parse_journal(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.JOURNAL_ARTICLE
    assert ref.authors[0].family == "Smith"
    assert ref.authors[0].given_initials == "J. K."
    assert ref.year == "2020"
    assert ref.title == "The effects of A on B"
    assert ref.container == "Journal of Things"
    assert ref.volume == "5"
    assert ref.issue == "2"
    assert ref.pages == "100-120"
    assert ref.doi == "10.1234/jot.2020.05"


def test_parses_journal_with_two_authors_and_no_doi():
    raw = "Smith, J., & Jones, A. (2019). A study. Nature Reviews, 12, 5-7."
    ref = try_parse_journal(raw, position_start=0)
    assert ref is not None
    assert [a.family for a in ref.authors] == ["Smith", "Jones"]
    assert ref.year == "2019"
    assert ref.doi is None


def test_returns_none_for_clearly_non_journal():
    raw = "Smith, J. (2020). A book. Earth Press."
    # No volume/issue/pages — not a journal article.
    ref = try_parse_journal(raw, position_start=0)
    assert ref is None


def test_parses_journal_with_doi_colon_prefix():
    raw = "Smith, J. (2020). A paper. Journal of Things, 5(2), 100-120. doi:10.1234/jot.2020.05"
    ref = try_parse_journal(raw, position_start=0)
    assert ref is not None
    assert ref.doi == "10.1234/jot.2020.05"
