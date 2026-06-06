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


def test_parses_news_website_without_separate_container():
    raw = (
        "Bloomberg. (2024, July 11). Nestlé's scaled-back recycling goals. "
        "https://www.bloomberg.com/news/features/2024-07-11/test"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.WEBSITE
    assert ref.authors[0].family == "Bloomberg"
    assert ref.year == "2024"
    assert ref.url == "https://www.bloomberg.com/news/features/2024-07-11/test"


def test_parses_website_with_nd_letter():
    raw = (
        "Saba, O. (n.d.-a). Equality, Diversity and Inclusion. "
        "UTS College Canvas. https://canvas.utscollege.edu.au/courses/7847"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.year == "n.d.-a"


def test_parses_news_website_with_parenthetical_date():
    raw = (
        "Apple Newsroom. (2025, November 6). Apple announces new renewable energy "
        "projects. https://www.apple.com/newsroom/test"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.authors[0].family == "Apple Newsroom"
    assert ref.year == "2025"
