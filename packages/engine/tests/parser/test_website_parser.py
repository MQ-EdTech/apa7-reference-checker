from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.website import try_parse_website


def test_parses_basic_webpage_with_n_d():
    raw = (
        "World Health Organization. (n.d.). Climate change and health. "
        "WHO. https://www.who.int/climate"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.WEBSITE
    assert ref.year == "n.d."
    assert ref.title == "Climate change and health"
    assert ref.url == "https://www.who.int/climate"
    assert ref.container == "WHO"


def test_parses_webpage_with_date():
    raw = "Doe, J. (2022, March 5). A web article. Some Site. https://example.com/post"
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.year == "2022"
    assert ref.url == "https://example.com/post"
