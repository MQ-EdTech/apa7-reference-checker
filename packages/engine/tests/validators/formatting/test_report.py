# packages/engine/tests/validators/formatting/test_report.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.report import check_report


def _report(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.REPORT,
        authors=[Author(family="ABS", given_initials="")],
        year="2023",
        title="Population trends",
        publisher="ABS",
        extras={"report_number": "3101.0"},
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_report_has_no_issues():
    assert check_report(_report()) == []


def test_missing_publisher_emits_error():
    issues = check_report(_report(publisher=None))
    assert any(i.code == "report_missing_publisher" for i in issues)
