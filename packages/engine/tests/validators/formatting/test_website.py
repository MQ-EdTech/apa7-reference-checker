# packages/engine/tests/validators/formatting/test_website.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.website import check_website


def _site(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.WEBSITE,
        authors=[Author(family="WHO", given_initials="")],
        year="2022",
        title="A page",
        container="WHO",
        url="https://who.int/x",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_site_has_no_issues():
    assert check_website(_site()) == []


def test_missing_url_emits_error():
    issues = check_website(_site(url=None))
    assert any(i.code == "website_missing_url" for i in issues)


def test_no_date_emits_retrieval_info_when_not_archived():
    issues = check_website(_site(year="n.d.", url="https://example.com/live"))
    assert any(i.code == "website_consider_retrieval_date" for i in issues)


def test_no_date_archived_url_does_not_emit_retrieval_hint():
    issues = check_website(_site(year="n.d.", url="https://web.archive.org/web/2023*/example.com"))
    assert all(i.code != "website_consider_retrieval_date" for i in issues)
