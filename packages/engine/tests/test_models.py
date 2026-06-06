from apa7_validator.models import (
    Author,
    Citation,
    Issue,
    Position,
    Reference,
    ReferenceType,
    Report,
    Severity,
)


def test_reference_minimal_fields():
    ref = Reference(
        raw="Smith, J. (2020). A paper. Journal of Things, 1(2), 3-4.",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        position=Position(start=0, end=58),
    )
    assert ref.ref_type is ReferenceType.JOURNAL_ARTICLE
    assert ref.authors[0].family == "Smith"
    assert ref.year == "2020"


def test_citation_with_page_number():
    cit = Citation(
        raw="(Smith, 2020, p. 5)",
        authors=["Smith"],
        year="2020",
        page="5",
        narrative=False,
        position=Position(start=100, end=119),
    )
    assert cit.page == "5"
    assert cit.narrative is False
    assert cit.secondary_source_author is None


def test_issue_carries_severity_and_span():
    iss = Issue(
        code="doi_not_found",
        severity=Severity.ERROR,
        message="DOI not found in CrossRef",
        position=Position(start=42, end=58),
        suggestion="Verify the DOI prefix and suffix",
    )
    assert iss.severity is Severity.ERROR
    assert iss.target_kind == "reference"


def test_report_aggregates_issues():
    rep = Report(
        references=[],
        citations=[],
        issues=[],
        warnings=[],
        degraded_checks=[],
    )
    assert rep.issues == []
