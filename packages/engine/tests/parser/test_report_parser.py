from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.report import try_parse_report


def test_parses_government_report_with_number():
    raw = "Australian Bureau of Statistics. (2023). Population trends (Report No. 3101.0). ABS."
    ref = try_parse_report(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.REPORT
    assert ref.title == "Population trends"
    assert ref.publisher == "ABS"
    assert ref.extras.get("report_number") == "3101.0"


def test_parses_report_without_number():
    raw = "OECD. (2021). Education at a glance. OECD Publishing."
    ref = try_parse_report(raw, position_start=0)
    assert ref is not None
    assert ref.publisher == "OECD Publishing"


def test_does_not_misclassify_book_containing_un_substring():
    # "Foundations" contains lowercase 'un' — used to false-positive the
    # case-insensitive UN hint and route to the report parser.
    raw = "Smith, J. (2020). Foundations of climate research. Earth Press."
    assert try_parse_report(raw, position_start=0) is None


def test_does_not_misclassify_book_containing_who_substring():
    # "Whole" or "whose" used to false-positive the case-insensitive WHO hint.
    raw = "Smith, J. (2020). The whole story. Earth Press."
    assert try_parse_report(raw, position_start=0) is None


def test_un_acronym_in_authority_position_still_matches():
    raw = "UN Statistics Division. (2022). World population prospects. UN."
    ref = try_parse_report(raw, position_start=0)
    assert ref is not None
