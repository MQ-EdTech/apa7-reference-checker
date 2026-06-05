import asyncio

import pytest
from apa7_validator.clients.base import Clients, LookupResult


def test_lookup_result_found_carries_metadata():
    r = LookupResult.found({"title": "x"})
    assert r.status == "found"
    assert r.metadata == {"title": "x"}


def test_lookup_result_not_found():
    assert LookupResult.not_found().status == "not_found"


def test_lookup_result_unavailable():
    assert LookupResult.unavailable("offline").status == "unavailable"


def test_dry_run_clients_returns_unavailable_for_all():
    clients = Clients.dry_run()

    async def go() -> None:
        assert (await clients.crossref.lookup_doi("10.1234/abc")).status == "unavailable"
        assert (await clients.unpaywall.lookup_doi("10.1234/abc")).status == "unavailable"
        assert (await clients.openlibrary.lookup_isbn("9780000000000")).status == "unavailable"
        assert (await clients.url_check.check("https://example.com")).status == "unavailable"

    asyncio.run(go())


def test_clients_construction_rejects_text_like_args():
    with pytest.raises(TypeError):
        # The whole point of dry_run: don't accept content-bearing params anywhere.
        Clients.dry_run().crossref.lookup_doi("10.1234/abc", text="hi")  # type: ignore[call-arg]
