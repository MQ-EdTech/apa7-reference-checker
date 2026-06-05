# packages/engine/src/apa7_validator/validators/formatting/journal.py
from __future__ import annotations

from ...models import Issue, Reference, ReferenceType
from ..base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_journal(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.JOURNAL_ARTICLE:
        return []
    issues: list[Issue] = []
    if not ref.volume:
        issues.append(
            _B.error(
                code="journal_missing_volume",
                message="Journal article is missing a volume number",
                position=ref.position,
                suggestion="Add the volume number after the journal name: 'Journal Name, 5(2), 100-120'",
            )
        )
    if not ref.pages:
        issues.append(
            _B.warning(
                code="journal_missing_pages",
                message="Journal article is missing a page range",
                position=ref.position,
                suggestion="Add a page range or article identifier (e.g., 100-120 or e12345)",
            )
        )
    if not ref.doi:
        issues.append(
            _B.info(
                code="journal_missing_doi",
                message="Journal article is missing a DOI",
                position=ref.position,
                suggestion="Include the DOI as 'https://doi.org/10.xxxx/yyyy' when one is available",
            )
        )
    return issues
