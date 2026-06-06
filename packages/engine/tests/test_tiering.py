from apa7_validator.models import (
    Author,
    Position,
    Reference,
    ReferenceType,
)
from apa7_validator.tiering import classify_tier


def _ref(ref_type: ReferenceType) -> Reference:
    return Reference(
        raw="x",
        ref_type=ref_type,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="x",
        position=Position(0, 1),
    )


def test_journal_article_is_tier_1():
    assert classify_tier(_ref(ReferenceType.JOURNAL_ARTICLE)) == 1


def test_book_is_tier_1():
    assert classify_tier(_ref(ReferenceType.BOOK)) == 1


def test_book_chapter_is_tier_1():
    assert classify_tier(_ref(ReferenceType.BOOK_CHAPTER)) == 1


def test_website_is_tier_3():
    assert classify_tier(_ref(ReferenceType.WEBSITE)) == 3


def test_report_is_tier_3_in_v1():
    # In v1 Reports are Tier 3; in v1.1 they will likely move to Tier 2.
    assert classify_tier(_ref(ReferenceType.REPORT)) == 3


def test_ai_source_is_tier_3():
    assert classify_tier(_ref(ReferenceType.AI_SOURCE)) == 3


def test_unknown_is_tier_3():
    assert classify_tier(_ref(ReferenceType.UNKNOWN)) == 3
