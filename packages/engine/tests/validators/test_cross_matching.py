# packages/engine/tests/validators/test_cross_matching.py
from apa7_validator.models import Author, Citation, Position, Reference, ReferenceType
from apa7_validator.validators.cross_matching import check_cross_matching


def _ref(family: str, year: str) -> Reference:
    return Reference(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year=year,
        title="A paper",
        position=Position(0, 1),
    )


def _cit(family: str, year: str, narrative: bool = False) -> Citation:
    return Citation(
        raw="x",
        authors=[family],
        year=year,
        narrative=narrative,
        position=Position(0, 1),
    )


def test_clean_pair_has_no_issues():
    refs = [_ref("Smith", "2020")]
    cits = [_cit("Smith", "2020")]
    assert check_cross_matching(cits, refs) == []


def test_citation_without_reference_emits_error():
    issues = check_cross_matching([_cit("Smith", "2020")], [])
    assert any(i.code == "citation_without_reference" for i in issues)


def test_reference_uncited_emits_warning():
    issues = check_cross_matching([], [_ref("Smith", "2020")])
    assert any(i.code == "reference_uncited" for i in issues)


def test_et_al_matches_first_author():
    refs = [_ref("Smith", "2020")]
    cits = [
        Citation(
            raw="(Smith et al., 2020)",
            authors=["Smith et al."],
            year="2020",
            narrative=False,
            position=Position(0, 1),
        )
    ]
    assert check_cross_matching(cits, refs) == []


def test_ambiguous_match_emits_warning():
    refs = [_ref("Smith", "2020"), _ref("Smith", "2020")]
    cits = [_cit("Smith", "2020")]
    issues = check_cross_matching(cits, refs)
    assert any(i.code == "ambiguous_match" for i in issues)
