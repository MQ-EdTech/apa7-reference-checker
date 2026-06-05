# packages/engine/tests/test_api_validate.py
from apa7_validator import validate
from apa7_validator.clients import Clients


def test_validate_text_with_clean_input_returns_report():
    text = (
        "Climate change is well documented (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    report = validate(text, "text", clients=Clients.dry_run())
    assert len(report.references) == 1
    assert len(report.citations) == 1
    # cross-matching is clean
    assert all(i.code != "citation_without_reference" for i in report.issues)


def test_validate_text_flags_orphan_citation():
    text = "Climate is warming (Jones, 2021)."
    report = validate(text, "text", clients=Clients.dry_run())
    assert any(i.code == "citation_without_reference" for i in report.issues)
