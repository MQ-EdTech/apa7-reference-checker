# packages/engine/tests/validators/formatting/test_ai_source.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.ai_source import check_ai_source


def _ai(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.AI_SOURCE,
        authors=[Author(family="OpenAI", given_initials="")],
        year="2023",
        title="ChatGPT (Mar 14 version)",
        url="https://chat.openai.com/chat",
        extras={"model_kind": "Large language model"},
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_ai_source_has_no_issues():
    assert check_ai_source(_ai()) == []


def test_missing_model_kind_emits_error():
    issues = check_ai_source(_ai(extras={}))
    assert any(i.code == "ai_missing_model_kind" for i in issues)


def test_missing_url_emits_error():
    issues = check_ai_source(_ai(url=None))
    assert any(i.code == "ai_missing_url" for i in issues)


def test_personal_name_as_author_warns():
    issues = check_ai_source(_ai(authors=[Author(family="Smith", given_initials="J.")]))
    assert any(i.code == "ai_author_should_be_developer" for i in issues)
