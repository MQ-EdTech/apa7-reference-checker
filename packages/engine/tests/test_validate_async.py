"""validate_async returns the same Report as validate on the same input."""

from apa7_validator import validate, validate_async
from apa7_validator.clients import Clients


def test_async_matches_sync_on_clean_input():
    import asyncio

    text = (
        "Climate is warming (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    sync_report = validate(text, "text", clients=Clients.dry_run())
    async_report = asyncio.run(validate_async(text, "text", clients=Clients.dry_run()))

    # Compare the salient fields. Reports include lists of frozen dataclasses,
    # which compare by value.
    assert sync_report.references == async_report.references
    assert sync_report.citations == async_report.citations
    assert sync_report.issues == async_report.issues
    assert sync_report.warnings == async_report.warnings
    assert sync_report.degraded_checks == async_report.degraded_checks


def test_async_matches_sync_with_orphan_citation():
    import asyncio

    text = "Climate is warming (Jones, 2099)."
    sync_report = validate(text, "text", clients=Clients.dry_run())
    async_report = asyncio.run(validate_async(text, "text", clients=Clients.dry_run()))
    assert sync_report.issues == async_report.issues
