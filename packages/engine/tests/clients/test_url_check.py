import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]
from apa7_validator.clients.url_check import HttpxUrlCheckClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
)


@pytest.mark.asyncio
@my_vcr.use_cassette("url_check_alive.yaml")
async def test_live_url_returns_found():
    client = HttpxUrlCheckClient()
    result = await client.check("https://example.com")
    assert result.status == "found"


@pytest.mark.asyncio
@my_vcr.use_cassette("url_check_404.yaml")
async def test_404_url_returns_not_found():
    client = HttpxUrlCheckClient()
    result = await client.check("https://www.google.com/this-page-should-not-exist-apa7test")
    assert result.status == "not_found"
