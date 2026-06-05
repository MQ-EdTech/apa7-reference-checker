# packages/engine/tests/validators/test_existence.py
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from apa7_validator.clients.base import Clients, LookupResult
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.existence import check_existence


@dataclass
class _StubClient:
    impl: Callable[..., LookupResult]

    async def lookup_doi(self, doi: str) -> LookupResult:
        return self.impl(doi)

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        return self.impl(isbn)

    async def check(self, url: str) -> LookupResult:
        return self.impl(url)


def _clients(impl: Callable[..., LookupResult]) -> Clients:
    c = _StubClient(impl=impl)
    return Clients(crossref=c, unpaywall=c, openlibrary=c, url_check=c)


def _ref_with_doi(doi: str) -> Reference:
    return Reference(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="x",
        doi=doi,
        position=Position(0, 1),
    )


@pytest.mark.asyncio
async def test_found_doi_emits_no_issue():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, degraded = await check_existence(refs, _clients(lambda _id: LookupResult.found({})))
    assert issues == []
    assert degraded == []


@pytest.mark.asyncio
async def test_not_found_doi_emits_error():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, _ = await check_existence(refs, _clients(lambda _id: LookupResult.not_found()))
    assert any(i.code == "doi_not_found" for i in issues)


@pytest.mark.asyncio
async def test_unavailable_doi_emits_info_and_records_degradation():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, degraded = await check_existence(
        refs, _clients(lambda _id: LookupResult.unavailable("offline"))
    )
    assert any(i.code == "existence_check_unavailable" for i in issues)
    assert "existence" in degraded
