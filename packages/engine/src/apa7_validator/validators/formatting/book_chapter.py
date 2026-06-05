# packages/engine/src/apa7_validator/validators/formatting/book_chapter.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_book_chapter(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.BOOK_CHAPTER:
        return []
    issues: list[Issue] = []
    if not ref.extras.get("editors"):
        issues.append(
            _B.error(
                code="chapter_missing_editor",
                message="Book chapter is missing editor information ('In X (Ed.), Title')",
                position=ref.position,
                suggestion="Add 'In <Editor Name> (Ed.), <Book Title>' before the page range",
            )
        )
    if not ref.container:
        issues.append(
            _B.error(
                code="chapter_missing_book_title",
                message="Book chapter is missing the containing book title",
                position=ref.position,
                suggestion="Include the book title after 'In <Editor> (Ed.),'",
            )
        )
    if not ref.pages:
        issues.append(
            _B.error(
                code="chapter_missing_pages",
                message="Book chapter is missing a page range",
                position=ref.position,
                suggestion="Include the chapter's page range: '(pp. 100-120)'",
            )
        )
    if not ref.publisher:
        issues.append(
            _B.error(
                code="chapter_missing_publisher",
                message="Book chapter is missing the publisher",
                position=ref.position,
                suggestion="Include the publisher after the page range",
            )
        )
    return issues
