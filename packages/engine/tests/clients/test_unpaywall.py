import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]
from apa7_validator.clients.unpaywall import HttpxUnpaywallClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
    filter_query_parameters=["email"],
)


@pytest.mark.asyncio
@my_vcr.use_cassette("unpaywall_found_oa.yaml")
async def test_known_oa_doi_returns_found_with_oa_metadata():
    client = HttpxUnpaywallClient(contact_email="test@example.com")
    result = await client.lookup_doi("10.7717/peerj.4375")
    assert result.status == "found"
    assert "is_oa" in result.metadata


@pytest.mark.asyncio
@my_vcr.use_cassette("unpaywall_not_found.yaml")
async def test_unknown_doi_returns_not_found():
    client = HttpxUnpaywallClient(contact_email="test@example.com")
    result = await client.lookup_doi("10.9999/no-such-doi")
    assert result.status == "not_found"
