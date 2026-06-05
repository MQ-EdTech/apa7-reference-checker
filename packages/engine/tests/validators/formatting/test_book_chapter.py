# packages/engine/tests/validators/formatting/test_book_chapter.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.book_chapter import check_book_chapter


def _chapter(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.BOOK_CHAPTER,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A chapter",
        container="A Book",
        pages="100-120",
        publisher="Earth Press",
        extras={"editors": "K. Editor"},
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_chapter_has_no_issues():
    assert check_book_chapter(_chapter()) == []


def test_missing_editor_emits_error():
    issues = check_book_chapter(_chapter(extras={}))
    assert any(i.code == "chapter_missing_editor" for i in issues)


def test_missing_container_emits_error():
    issues = check_book_chapter(_chapter(container=None))
    assert any(i.code == "chapter_missing_book_title" for i in issues)


def test_missing_pages_emits_error():
    issues = check_book_chapter(_chapter(pages=None))
    assert any(i.code == "chapter_missing_pages" for i in issues)


def test_missing_publisher_emits_error():
    issues = check_book_chapter(_chapter(publisher=None))
    assert any(i.code == "chapter_missing_publisher" for i in issues)
