# packages/engine/tests/annotators/test_web.py
from apa7_validator.annotators.web import build_web_annotation
from apa7_validator.models import Issue, Position, Report, Severity


def test_web_annotation_shape():
    rep = Report(
        references=[],
        citations=[],
        issues=[Issue(code="x", severity=Severity.ERROR, message="m", position=Position(5, 10))],
        warnings=["no_reference_list_found"],
        degraded_checks=["existence"],
    )
    out = build_web_annotation(rep, source_text="0123456789ABC")
    assert out["warnings"] == ["no_reference_list_found"]
    assert out["degraded_checks"] == ["existence"]
    assert out["annotations"][0]["span"] == [5, 10]
    assert out["annotations"][0]["span_text"] == "56789"
    assert out["annotations"][0]["severity"] == "error"
