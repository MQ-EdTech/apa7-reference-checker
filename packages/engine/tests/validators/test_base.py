from apa7_validator.models import Position, Severity
from apa7_validator.validators.base import IssueBuilder, Rule


def test_issue_builder_emits_well_formed_issue():
    b = IssueBuilder(target_kind="reference")
    iss = b.error(code="bad_thing", message="bad", position=Position(0, 5))
    assert iss.severity is Severity.ERROR
    assert iss.code == "bad_thing"
    assert iss.target_kind == "reference"


def test_rule_protocol_is_satisfied_by_callable():
    def my_rule(ref):
        return []

    rule: Rule = my_rule
    assert rule
