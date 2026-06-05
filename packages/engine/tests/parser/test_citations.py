from apa7_validator.parser.citations import parse_citations


def test_parses_basic_parenthetical():
    text = "Climate is warming (Smith, 2020)."
    cits = parse_citations(text)
    assert len(cits) == 1
    assert cits[0].authors == ["Smith"]
    assert cits[0].year == "2020"
    assert cits[0].narrative is False


def test_parses_parenthetical_with_page():
    text = "As argued (Smith, 2020, p. 5), this is true."
    cits = parse_citations(text)
    assert cits[0].page == "5"


def test_parses_narrative_citation():
    text = "Smith (2020) argued that climate is warming."
    cits = parse_citations(text)
    assert len(cits) == 1
    assert cits[0].authors == ["Smith"]
    assert cits[0].year == "2020"
    assert cits[0].narrative is True


def test_parses_two_authors_with_ampersand():
    text = "(Smith & Jones, 2021) found new results."
    cits = parse_citations(text)
    assert cits[0].authors == ["Smith", "Jones"]


def test_parses_et_al_form():
    text = "(Smith et al., 2022) showed this."
    cits = parse_citations(text)
    assert cits[0].authors == ["Smith et al."]


def test_parses_secondary_source_marker():
    text = "(Brown, 2010, as cited in Smith, 2020)"
    cits = parse_citations(text)
    assert cits[0].secondary_source_author == "Brown"
    assert cits[0].year == "2020"  # the citing source's year, not the primary


def test_ignores_non_citation_parens():
    text = "There were many results (most positive) overall."
    cits = parse_citations(text)
    assert cits == []
