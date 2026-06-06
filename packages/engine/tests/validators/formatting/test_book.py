# packages/engine/tests/validators/formatting/test_book.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.book import check_book


def _book(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A book",
        publisher="Earth Press",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_book_has_no_issues():
    assert check_book(_book()) == []


def test_missing_publisher_emits_error():
    issues = check_book(_book(publisher=None))
    assert any(i.code == "book_missing_publisher" for i in issues)
