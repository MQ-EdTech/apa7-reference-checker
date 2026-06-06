from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

LookupStatus = Literal["found", "not_found", "unavailable"]


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    metadata: dict[str, Any] = field(default_factory=lambda: {})
    reason: str = ""

    @classmethod
    def found(cls, metadata: dict[str, Any]) -> LookupResult:
        return cls(status="found", metadata=metadata)

    @classmethod
    def not_found(cls) -> LookupResult:
        return cls(status="not_found")

    @classmethod
    def unavailable(cls, reason: str = "") -> LookupResult:
        return cls(status="unavailable", reason=reason)


class CrossRefClient(Protocol):
    async def lookup_doi(self, doi: str) -> LookupResult: ...


class UnpaywallClient(Protocol):
    async def lookup_doi(self, doi: str) -> LookupResult: ...


class OpenLibraryClient(Protocol):
    async def lookup_isbn(self, isbn: str) -> LookupResult: ...


class UrlCheckClient(Protocol):
    async def check(self, url: str) -> LookupResult: ...


class _DryClient:
    async def lookup_doi(self, doi: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")

    async def check(self, url: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")


@dataclass(frozen=True, slots=True)
class Clients:
    crossref: CrossRefClient
    unpaywall: UnpaywallClient
    openlibrary: OpenLibraryClient
    url_check: UrlCheckClient

    @classmethod
    def dry_run(cls) -> Clients:
        dry = _DryClient()
        return cls(crossref=dry, unpaywall=dry, openlibrary=dry, url_check=dry)
