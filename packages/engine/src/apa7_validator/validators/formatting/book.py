# packages/engine/src/apa7_validator/validators/formatting/book.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_book(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.BOOK:
        return []
    issues: list[Issue] = []
    if not ref.publisher:
        issues.append(
            _B.error(
                code="book_missing_publisher",
                message="Book reference is missing the publisher",
                position=ref.position,
                suggestion="Include the publisher after the title: 'Title. Publisher.'",
            )
        )
    return issues
