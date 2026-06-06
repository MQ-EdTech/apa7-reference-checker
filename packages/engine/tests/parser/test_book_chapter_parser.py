from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.book_chapter import try_parse_book_chapter


def test_parses_book_chapter_with_editor_marker():
    raw = (
        "Smith, J. (2020). A chapter title. In K. Editor (Ed.), "
        "Book title (pp. 100-120). Earth Press."
    )
    ref = try_parse_book_chapter(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.BOOK_CHAPTER
    assert ref.authors[0].family == "Smith"
    assert ref.title == "A chapter title"
    assert ref.container == "Book title"
    assert ref.pages == "100-120"
    assert ref.publisher == "Earth Press"


def test_rejects_journal_shape():
    raw = "Smith, J. (2020). A paper. Journal, 5(2), 100-120."
    assert try_parse_book_chapter(raw, position_start=0) is None
