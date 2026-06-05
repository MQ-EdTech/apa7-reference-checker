# packages/engine/src/apa7_validator/validators/formatting/website.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")
_ARCHIVED = ("archive.org", "web.archive.org")


def check_website(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.WEBSITE:
        return []
    issues: list[Issue] = []
    if not ref.url:
        issues.append(
            _B.error(
                code="website_missing_url",
                message="Website reference is missing a URL",
                position=ref.position,
                suggestion="Include the page URL at the end of the reference",
            )
        )
    if ref.year == "n.d." and ref.url and not any(host in ref.url for host in _ARCHIVED):
        issues.append(
            _B.info(
                code="website_consider_retrieval_date",
                message="Source with no date that may change over time: consider including a retrieval date",
                position=ref.position,
                suggestion="Format: 'Retrieved <Month Day, Year>, from <URL>' before the URL",
            )
        )
    return issues
