# packages/engine/tests/test_logging.py
import pytest
from apa7_validator.logging import SAFE_FIELDS, safe_log


def test_allowed_fields_accepted(capsys):
    safe_log("job started", job_id="abc", status="pending")
    captured = capsys.readouterr()
    assert "abc" in captured.out


def test_disallowed_field_raises():
    with pytest.raises(ValueError):
        safe_log("oops", essay="this should never log")


def test_safe_fields_includes_expected_keys():
    expected = {
        "job_id",
        "status",
        "duration_ms",
        "error_code",
        "reference_count",
        "issue_count",
        "degraded_checks",
    }
    assert expected <= SAFE_FIELDS
