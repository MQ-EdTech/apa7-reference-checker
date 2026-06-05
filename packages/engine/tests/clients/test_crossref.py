import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]
from apa7_validator.clients.crossref import HttpxCrossRefClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
    filter_headers=["authorization", "user-agent"],
)


@pytest.mark.asyncio
@my_vcr.use_cassette("crossref_found.yaml")
async def test_lookup_known_doi_returns_found():
    client = HttpxCrossRefClient(user_agent="apa7-validator-test/0.1 (test@example.com)")
    result = await client.lookup_doi("10.1037/0003-066X.59.1.29")
    assert result.status == "found"
    assert "title" in result.metadata


@pytest.mark.asyncio
@my_vcr.use_cassette("crossref_not_found.yaml")
async def test_lookup_unknown_doi_returns_not_found():
    client = HttpxCrossRefClient(user_agent="apa7-validator-test/0.1 (test@example.com)")
    result = await client.lookup_doi("10.9999/this-doi-does-not-exist")
    assert result.status == "not_found"
