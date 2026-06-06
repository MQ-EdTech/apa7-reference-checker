# packages/engine/src/apa7_validator/validators/existence.py
from __future__ import annotations

import asyncio

from ..clients.base import Clients, LookupResult
from ..models import Issue, Reference
from .base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


async def _check_one(ref: Reference, clients: Clients) -> list[Issue]:
    if ref.doi:
        result = await clients.crossref.lookup_doi(ref.doi)
        return _issues_from(result, ref, kind="doi")
    if ref.isbn:
        result = await clients.openlibrary.lookup_isbn(ref.isbn)
        return _issues_from(result, ref, kind="isbn")
    if ref.url:
        result = await clients.url_check.check(ref.url)
        return _issues_from(result, ref, kind="url")
    return []


def _issues_from(result: LookupResult, ref: Reference, *, kind: str) -> list[Issue]:
    if result.status == "found":
        return []
    if result.status == "not_found":
        return [
            _B.error(
                code=f"{kind}_not_found",
                message=f"{kind.upper()} not found in lookup service",
                position=ref.position,
                suggestion=f"Verify the {kind.upper()} value (typos are common)",
            )
        ]
    return [
        _B.info(
            code="existence_check_unavailable",
            message=f"Could not verify {kind.upper()} existence ({result.reason or 'unknown'})",
            position=ref.position,
            suggestion="Re-run the check when the lookup service is available",
        )
    ]


async def check_existence(
    refs: list[Reference],
    clients: Clients,
) -> tuple[list[Issue], list[str]]:
    """Returns (issues, degraded_checks). `existence` appears in degraded_checks
    if any reference's lookup returned `unavailable`."""
    results = await asyncio.gather(*[_check_one(ref, clients) for ref in refs])
    issues = [iss for sub in results for iss in sub]
    degraded = ["existence"] if any(i.code == "existence_check_unavailable" for i in issues) else []
    return issues, degraded
