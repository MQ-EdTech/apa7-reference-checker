# packages/engine/src/apa7_validator/validators/formatting/report.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_report(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.REPORT:
        return []
    issues: list[Issue] = []
    if not ref.publisher:
        issues.append(
            _B.error(
                code="report_missing_publisher",
                message="Report reference is missing the publisher / issuing organisation",
                position=ref.position,
                suggestion="Include the issuing body after the title (or after the report number)",
            )
        )
    return issues
