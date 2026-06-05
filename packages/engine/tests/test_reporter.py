# packages/engine/tests/test_reporter.py
from apa7_validator.models import Author, Citation, Position, Reference, ReferenceType, Severity
from apa7_validator.reporter import assemble


def _ref(family: str = "Smith") -> Reference:
    return Reference(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year="2020",
        title="x",
        position=Position(0, 1),
    )


def _cit() -> Citation:
    return Citation(
        raw="x", authors=["Smith"], year="2020", narrative=False, position=Position(0, 1)
    )


def test_assemble_packs_inputs_into_report():
    rep = assemble(
        references=[_ref()],
        citations=[_cit()],
        formatting_issues=[],
        cross_matching_issues=[],
        existence_issues=[],
        warnings=["no_reference_list_found"],
        degraded_checks=[],
    )
    assert rep.references[0].authors[0].family == "Smith"
    assert rep.warnings == ["no_reference_list_found"]


def test_issues_sorted_by_severity_then_position():
    from apa7_validator.models import Issue

    issues = [
        Issue(code="b", severity=Severity.WARNING, message="m", position=Position(0, 1)),
        Issue(code="a", severity=Severity.ERROR, message="m", position=Position(0, 1)),
    ]
    rep = assemble(
        references=[],
        citations=[],
        formatting_issues=issues,
        cross_matching_issues=[],
        existence_issues=[],
        warnings=[],
        degraded_checks=[],
    )
    assert rep.issues[0].severity is Severity.ERROR
