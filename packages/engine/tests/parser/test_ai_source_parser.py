from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.ai_source import try_parse_ai_source


def test_parses_chatgpt_reference():
    raw = (
        "OpenAI. (2023). ChatGPT (Mar 14 version) "
        "[Large language model]. https://chat.openai.com/chat"
    )
    ref = try_parse_ai_source(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.AI_SOURCE
    assert ref.title.startswith("ChatGPT")
    assert ref.url == "https://chat.openai.com/chat"
    assert ref.extras.get("model_kind") == "Large language model"


def test_rejects_non_ai_reference():
    raw = "Smith, J. (2020). A book. Earth Press."
    assert try_parse_ai_source(raw, position_start=0) is None
