# packages/engine/tests/test_structural_guarantees.py
"""Structural tests that fail CI if privacy guarantees are violated."""

import inspect
import pkgutil
import re
from pathlib import Path

import apa7_validator.clients as clients_pkg

FORBIDDEN_PARAM_NAMES = {"text", "essay", "body", "content", "extracted_text"}


def _iter_client_callables():
    for _finder, name, _ispkg in pkgutil.iter_modules(clients_pkg.__path__):
        mod = __import__(f"apa7_validator.clients.{name}", fromlist=["*"])
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if inspect.isclass(attr):
                for method_name, method in inspect.getmembers(attr, inspect.isfunction):
                    yield f"{name}.{attr_name}.{method_name}", method


def test_no_client_callable_accepts_text_like_params():
    violations: list[str] = []
    for full_name, fn in _iter_client_callables():
        sig = inspect.signature(fn)
        for pname in sig.parameters:
            if pname in FORBIDDEN_PARAM_NAMES:
                violations.append(f"{full_name} has forbidden param '{pname}'")
    assert not violations, "\n".join(violations)


_SRC = Path(__file__).parent.parent / "src" / "apa7_validator"
_BAD_LOGGER_CALLS = re.compile(
    r"""logger\.(?:info|debug|warning|error|critical)\([^)]*\b(?:essay|text|body|content)\s*=""",
    re.VERBOSE,
)


def test_source_does_not_log_forbidden_fields_directly():
    violations: list[str] = []
    for path in _SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for m in _BAD_LOGGER_CALLS.finditer(text):
            violations.append(f"{path}: {m.group(0)}")
    assert not violations, "\n".join(violations)
