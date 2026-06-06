from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.book import try_parse_book


def test_parses_basic_book():
    raw = "Smith, J. (2020). Foundations of climate research. Earth Press."
    ref = try_parse_book(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.BOOK
    assert ref.authors[0].family == "Smith"
    assert ref.year == "2020"
    assert ref.title == "Foundations of climate research"
    assert ref.publisher == "Earth Press"


def test_parses_book_with_doi():
    raw = "Brown, K. (2018). Statistical methods. Academic Press. https://doi.org/10.5555/spm.2018"
    ref = try_parse_book(raw, position_start=0)
    assert ref is not None
    assert ref.doi == "10.5555/spm.2018"
    assert ref.publisher == "Academic Press"


def test_rejects_journal_shape():
    raw = "Smith, J. (2020). A paper. Journal, 5(2), 100-120."
    ref = try_parse_book(raw, position_start=0)
    assert ref is None


def test_parses_book_with_doi_colon_prefix():
    raw = "Brown, K. (2018). Statistical methods. Academic Press. doi:10.5555/spm.2018"
    ref = try_parse_book(raw, position_start=0)
    assert ref is not None
    assert ref.doi == "10.5555/spm.2018"
