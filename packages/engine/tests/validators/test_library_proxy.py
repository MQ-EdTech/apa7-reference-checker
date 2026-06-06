from apa7_validator.models import (
    Author,
    Position,
    Reference,
    ReferenceType,
)
from apa7_validator.validators.library_proxy import check_library_proxy_url


def _ref(url: str = "", raw: str = "") -> Reference:
    return Reference(
        raw=raw or f"Smith, J. (2020). Title. Publisher. {url}",
        ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="Title",
        position=Position(0, 100),
        url=url or None,
    )


def test_flags_ebook_central_library_proxy():
    ref = _ref(url="https://ebookcentral.proquest.com/lib/uts/reader.action?docID=99707")
    issues = check_library_proxy_url(ref)
    assert any(i.code == "reference_uses_library_proxy_url" for i in issues)


def test_flags_proxy_in_raw_text_when_not_extracted():
    # The parser failed to extract URL, but the raw text has a proxy URL.
    ref = _ref(raw="Smith, J. (2020). Title. https://ebookcentral.proquest.com/lib/uts/test")
    # Ensure ref.url is None for this test path.
    ref_no_url = Reference(
        raw=ref.raw,
        ref_type=ref.ref_type,
        authors=ref.authors,
        year=ref.year,
        title=ref.title,
        position=ref.position,
        url=None,
    )
    issues = check_library_proxy_url(ref_no_url)
    assert any(i.code == "reference_uses_library_proxy_url" for i in issues)


def test_does_not_flag_canonical_doi():
    ref = _ref(url="https://doi.org/10.1234/abc")
    assert check_library_proxy_url(ref) == []


def test_does_not_flag_canvas_lms_url():
    # Canvas LMS URLs are intentionally NOT flagged in v1 (strict-mode for later).
    ref = _ref(url="https://canvas.utscollege.edu.au/courses/7847/pages/test")
    assert check_library_proxy_url(ref) == []


def test_does_not_flag_news_or_org_url():
    ref = _ref(url="https://www.bbc.com/news/test")
    assert check_library_proxy_url(ref) == []


def test_flags_ebsco_proxy():
    ref = _ref(url="https://web.b.ebscohost.com/ehost/detail/test")
    issues = check_library_proxy_url(ref)
    assert any(i.code == "reference_uses_library_proxy_url" for i in issues)


def test_flags_gale_library_proxy():
    ref = _ref(url="https://go.gale.com/ps/i.do?p=AONE&u=uts_main")
    issues = check_library_proxy_url(ref)
    assert any(i.code == "reference_uses_library_proxy_url" for i in issues)
