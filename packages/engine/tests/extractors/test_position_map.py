from apa7_validator.extractors.base import PositionMap


def test_to_source_returns_none_for_empty_entries_with_non_identity_kind():
    pm = PositionMap(kind="docx_run", entries=[])
    kind, ref = pm.to_source(5)
    assert kind == "docx_run"
    assert ref is None


def test_to_source_returns_offset_for_char_offset_kind():
    pm = PositionMap(kind="char_offset")
    assert pm.to_source(7) == ("char_offset", 7)
