# packages/engine/tests/validators/formatting/test_journal.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.journal import check_journal


def _journal(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        container="Journal of Things",
        volume="5",
        issue="2",
        pages="100-120",
        doi="10.1234/jot.2020.05",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_journal_has_no_issues():
    assert check_journal(_journal()) == []


def test_missing_volume_emits_error():
    issues = check_journal(_journal(volume=None))
    assert any(i.code == "journal_missing_volume" for i in issues)


def test_missing_pages_emits_warning():
    issues = check_journal(_journal(pages=None))
    assert any(i.code == "journal_missing_pages" for i in issues)


def test_missing_doi_emits_info():
    issues = check_journal(_journal(doi=None))
    assert any(i.code == "journal_missing_doi" for i in issues)
