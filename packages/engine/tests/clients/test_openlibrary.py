import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]
from apa7_validator.clients.openlibrary import HttpxOpenLibraryClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
)


@pytest.mark.asyncio
@my_vcr.use_cassette("openlibrary_found.yaml")
async def test_known_isbn_returns_found():
    client = HttpxOpenLibraryClient()
    result = await client.lookup_isbn("9780201896831")
    assert result.status == "found"


@pytest.mark.asyncio
@my_vcr.use_cassette("openlibrary_not_found.yaml")
async def test_unknown_isbn_returns_not_found():
    client = HttpxOpenLibraryClient()
    result = await client.lookup_isbn("0000000000000")
    assert result.status == "not_found"
