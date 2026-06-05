import inspect

import apa7_validator


def test_public_validate_is_exported():
    assert hasattr(apa7_validator, "validate")
    assert callable(apa7_validator.validate)


def test_public_annotate_docx_is_exported():
    assert hasattr(apa7_validator, "annotate_docx")
    assert callable(apa7_validator.annotate_docx)


def test_validate_signature():
    sig = inspect.signature(apa7_validator.validate)
    params = sig.parameters
    assert "source" in params
    assert "format" in params
    assert "clients" in params
    assert params["clients"].kind is inspect.Parameter.KEYWORD_ONLY
