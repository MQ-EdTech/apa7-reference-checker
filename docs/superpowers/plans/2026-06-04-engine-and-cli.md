# APA 7 Reference Checker — Engine + CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `apa7_validator` (Python library) and `apa7-check` (CLI) that validate APA 7 references and in-text citations in `.docx`/`.pdf`/text inputs, producing structured `Report`s and annotated DOCX outputs.

**Architecture:** Library-first. Pure-Python engine with no HTTP, no DB, no LMS knowledge. All IO (file reading, HTTP lookups) is at the engine boundary via injectable client objects with dry-run modes for tests. Three internal layers — extractors (input → text + position map), parser (text → structured `Reference`/`Citation`), validators (structured data → issues) — feed a `reporter` that assembles a `Report`. Annotators consume the `Report` to produce SPA-friendly JSON or Word-native comments on a DOCX. The CLI is a thin `typer` wrapper around the library's public API.

**Tech Stack:** Python 3.12+, `uv` workspaces, `hatchling` build backend, `pytest` + `pytest-asyncio` + `pytest-mock` + `syrupy`, `vcrpy` (HTTP cassettes), `httpx` (async HTTP), `ruff` (lint + format), `pyright` (types), `python-docx` (DOCX reading), `lxml` (direct OOXML for comment injection), `pymupdf` (PDF text extraction), `typer` (CLI), `structlog` (structured logging), stdlib `dataclasses`.

**Spec reference:** `docs/superpowers/specs/2026-06-04-apa7-reference-checker-design.md` §5.1, §5.5, §6.3, §7, §8, §9.3, §9.4, §10.

---

## Phase organisation

The plan runs in three sequential phases. Each phase ends with a runnable artifact that can be exercised and reviewed before moving on.

| Phase | Tasks | Output |
|---|---|---|
| **A — Foundation** | 1–15 | `apa7_validator.extract()` + `apa7_validator.parse()` produce structured `Reference[]` and `Citation[]` from text/DOCX/PDF inputs. |
| **B — Validation** | 16–32 | `apa7_validator.validate()` produces a complete `Report` including formatting, cross-matching, and (network-aware) existence findings. |
| **C — Output + CLI** | 33–45 | `apa7_validator.annotate_docx()` produces a Word-comment-annotated `.docx`. `apa7-check` CLI exposes everything from the shell. End-to-end smoke test passes. |

---

## File Structure

Created during this plan (under the project root):

```
.github/
└── workflows/
    └── ci.yml                              # Task 2

.pre-commit-config.yaml                     # Task 2
.env.example                                # Task 2
pyproject.toml                              # Task 1 (workspace root)
README.md                                   # Task 45
CONTRIBUTING.md                             # Task 45

packages/engine/
├── pyproject.toml                          # Task 1
├── README.md                               # Task 45
├── src/apa7_validator/
│   ├── __init__.py                         # Task 4 (public exports)
│   ├── api.py                              # Task 4 (validate, annotate_docx)
│   ├── models.py                           # Task 3
│   ├── logging.py                          # Task 31
│   ├── extractors/
│   │   ├── __init__.py                     # Task 5
│   │   ├── base.py                         # Task 5
│   │   ├── text.py                         # Task 5
│   │   ├── docx.py                         # Task 6
│   │   └── pdf.py                          # Task 7
│   ├── parser/
│   │   ├── __init__.py                     # Task 8
│   │   ├── reference_list.py               # Task 8
│   │   ├── references.py                   # Task 9
│   │   ├── ref_types/
│   │   │   ├── __init__.py                 # Task 9
│   │   │   ├── journal.py                  # Task 9
│   │   │   ├── book.py                     # Task 10
│   │   │   ├── book_chapter.py             # Task 11
│   │   │   ├── website.py                  # Task 12
│   │   │   ├── report.py                   # Task 13
│   │   │   └── ai_source.py                # Task 14
│   │   └── citations.py                    # Task 15
│   ├── validators/
│   │   ├── __init__.py                     # Task 16
│   │   ├── base.py                         # Task 16
│   │   ├── formatting/
│   │   │   ├── __init__.py                 # Task 17
│   │   │   ├── cross_cutting.py            # Task 17
│   │   │   ├── journal.py                  # Task 18
│   │   │   ├── book.py                     # Task 19
│   │   │   ├── book_chapter.py             # Task 20
│   │   │   ├── website.py                  # Task 21
│   │   │   ├── report.py                   # Task 22
│   │   │   └── ai_source.py                # Task 23
│   │   ├── cross_matching.py               # Task 24
│   │   └── existence.py                    # Task 30
│   ├── clients/
│   │   ├── __init__.py                     # Task 25
│   │   ├── base.py                         # Task 25
│   │   ├── crossref.py                     # Task 26
│   │   ├── unpaywall.py                    # Task 27
│   │   ├── openlibrary.py                  # Task 28
│   │   └── url_check.py                    # Task 29
│   ├── annotators/
│   │   ├── __init__.py                     # Task 33
│   │   ├── web.py                          # Task 33
│   │   └── docx.py                         # Task 34/35/36
│   └── reporter.py                         # Task 32
└── tests/
    ├── conftest.py                         # Task 3
    ├── fixtures/
    │   ├── docx/sample_essay.docx          # Task 6
    │   ├── pdf/sample_essay.pdf            # Task 7
    │   └── cassettes/                      # Task 26+
    ├── extractors/                         # Tasks 5–7
    ├── parser/                             # Tasks 8–15
    ├── validators/                         # Tasks 16–24, 30
    ├── clients/                            # Tasks 25–29
    ├── annotators/                         # Tasks 33–36
    ├── test_reporter.py                    # Task 32
    ├── test_api.py                         # Task 37/38
    ├── test_structural_guarantees.py       # Task 39/40
    └── test_end_to_end.py                  # Task 44

packages/cli/
├── pyproject.toml                          # Task 41
├── src/apa7_check/
│   ├── __init__.py                         # Task 41
│   ├── main.py                             # Task 41
│   └── render.py                           # Task 42
└── tests/
    ├── test_cli_basic.py                   # Task 41
    ├── test_cli_json.py                    # Task 42
    └── test_cli_annotate.py                # Task 43
```

---

## Conventions used by every task

- **Working directory:** project root (`/Users/aaron/codebase/active/APA7-reference checker`) unless otherwise noted.
- **TDD discipline:** every task starts with a failing test (when applicable), then minimal implementation, then a green test, then commit. Tests use `pytest`.
- **Commits:** Conventional Commits style (`feat:`, `test:`, `refactor:`, `chore:`, `docs:`). One logical change per commit. Frequent commits are explicitly preferred.
- **Branch:** stay on `main` (single contributor, no remote yet); a feature branch is unnecessary for this phase.
- **`uv run`:** all Python invocations go through `uv run` to ensure the workspace virtualenv is used. Example: `uv run pytest packages/engine/tests/...`.
- **Test running:** unless a step says otherwise, `Run:` lines should be executed verbatim.
- **No emoji** in code, commit messages, or docs (per user's global preferences).
- **No `Co-Authored-By: Claude`** trailers or `🤖 Generated with [Claude Code]` footers in commit messages (per user's global preferences).

---

# Phase A — Foundation (Tasks 1–15)

End state: `apa7_validator` package importable; `extract()` produces `ExtractionResult` from text/DOCX/PDF; `parse_references()` and `parse_citations()` produce structured `Reference[]` and `Citation[]`.

---

### Task 1: Bootstrap monorepo workspace

**Files:**
- Create: `pyproject.toml` (workspace root)
- Create: `packages/engine/pyproject.toml`
- Create: `packages/engine/src/apa7_validator/__init__.py`
- Create: `packages/engine/tests/__init__.py`
- Modify: `.gitignore` (already exists; verify `__pycache__/`, `.venv/` are listed)

- [ ] **Step 1: Verify uv is installed**

Run: `uv --version`
Expected: prints a version string (e.g., `uv 0.5.0`). If not installed, install via `curl -LsSf https://astral.sh/uv/install.sh | sh` and re-run.

- [ ] **Step 2: Create the workspace root `pyproject.toml`**

```toml
# pyproject.toml
[project]
name = "apa7-reference-checker"
version = "0.0.0"
description = "APA 7 reference and citation validator (workspace root)"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/engine", "packages/cli"]

[tool.uv.sources]
apa7-validator = { workspace = true }
apa7-check = { workspace = true }

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "RUF", "ASYNC"]
ignore = ["E501"]  # line-length handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
include = ["packages/engine/src", "packages/cli/src"]
```

- [ ] **Step 3: Create the engine package `pyproject.toml`**

```toml
# packages/engine/pyproject.toml
[project]
name = "apa7-validator"
version = "0.1.0"
description = "Pure-Python APA 7 reference and citation validator"
requires-python = ">=3.12"
dependencies = [
    "python-docx>=1.1.0",
    "pymupdf>=1.24.0",
    "lxml>=5.2.0",
    "httpx>=0.27.0",
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "syrupy>=4.6.0",
    "vcrpy>=6.0.0",
    "ruff>=0.5.0",
    "pyright>=1.1.360",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/apa7_validator"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: Create the engine `__init__.py` placeholders**

```python
# packages/engine/src/apa7_validator/__init__.py
"""APA 7 reference and citation validator."""

__version__ = "0.1.0"
```

```python
# packages/engine/tests/__init__.py
```

- [ ] **Step 5: Install the workspace**

Run: `uv sync --all-extras`
Expected: completes without error, prints a list of resolved + installed packages. Creates `.venv/` and `uv.lock`.

- [ ] **Step 6: Verify import works**

Run: `uv run python -c "import apa7_validator; print(apa7_validator.__version__)"`
Expected: prints `0.1.0`.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock packages/engine/pyproject.toml packages/engine/src/apa7_validator/__init__.py packages/engine/tests/__init__.py
git commit -m "chore: bootstrap uv workspace with apa7-validator engine package"
```

---

### Task 2: Pre-commit hooks + CI workflow

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/ci.yml`
- Create: `.env.example`

- [ ] **Step 1: Create the pre-commit config**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict

  - repo: local
    hooks:
      - id: forbid-mq-internal-strings
        name: forbid MQ-internal strings (mq.edu.au, OneID, student IDs)
        entry: bash -c 'if grep -rEn "mq\.edu\.au|OneID|s[0-9]{8}" --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" --include="*.toml" packages/ apps/ docs/ 2>/dev/null; then echo "Forbidden MQ-internal string detected"; exit 1; fi'
        language: system
        pass_filenames: false
```

- [ ] **Step 2: Create the CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-engine:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "0.5.x"
      - name: Install Python
        run: uv python install 3.12
      - name: Install workspace
        run: uv sync --all-extras
      - name: Lint
        run: uv run ruff check .
      - name: Format check
        run: uv run ruff format --check .
      - name: Type check
        run: uv run pyright packages/engine/src
      - name: Test engine
        run: uv run pytest packages/engine/tests -v
```

- [ ] **Step 3: Create `.env.example`**

```bash
# .env.example
# Contact email sent to Unpaywall (required by their API; not user PII).
UNPAYWALL_CONTACT_EMAIL=
# Optional: structlog log level. Default: INFO.
LOG_LEVEL=INFO
```

- [ ] **Step 4: Install pre-commit and run it once**

Run:
```bash
uv pip install pre-commit
uv run pre-commit install
uv run pre-commit run --all-files
```
Expected: hooks install; first run may fix trailing whitespace / EOFs and exit 1 (re-run to confirm green).

- [ ] **Step 5: Commit**

```bash
git add .pre-commit-config.yaml .github/workflows/ci.yml .env.example
git commit -m "chore: add pre-commit hooks (ruff, MQ-internal-string guard) and CI workflow"
```

---

### Task 3: Define core domain models

**Files:**
- Create: `packages/engine/src/apa7_validator/models.py`
- Create: `packages/engine/tests/conftest.py`
- Create: `packages/engine/tests/test_models.py`

- [ ] **Step 1: Write the failing test for `Reference` and `Citation`**

```python
# packages/engine/tests/test_models.py
from apa7_validator.models import (
    Author,
    Citation,
    Issue,
    Position,
    Reference,
    ReferenceType,
    Report,
    Severity,
)


def test_reference_minimal_fields():
    ref = Reference(
        raw="Smith, J. (2020). A paper. Journal of Things, 1(2), 3-4.",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        position=Position(start=0, end=58),
    )
    assert ref.ref_type is ReferenceType.JOURNAL_ARTICLE
    assert ref.authors[0].family == "Smith"
    assert ref.year == "2020"


def test_citation_with_page_number():
    cit = Citation(
        raw="(Smith, 2020, p. 5)",
        authors=["Smith"],
        year="2020",
        page="5",
        narrative=False,
        position=Position(start=100, end=119),
    )
    assert cit.page == "5"
    assert cit.narrative is False


def test_issue_carries_severity_and_span():
    iss = Issue(
        code="doi_not_found",
        severity=Severity.ERROR,
        message="DOI not found in CrossRef",
        position=Position(start=42, end=58),
        suggestion="Verify the DOI prefix and suffix",
    )
    assert iss.severity is Severity.ERROR


def test_report_aggregates_issues():
    rep = Report(
        references=[],
        citations=[],
        issues=[],
        warnings=[],
        degraded_checks=[],
    )
    assert rep.issues == []
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `uv run pytest packages/engine/tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apa7_validator.models'`.

- [ ] **Step 3: Create the models module**

```python
# packages/engine/src/apa7_validator/models.py
"""Core domain models. Pure dataclasses, no IO."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class ReferenceType(Enum):
    JOURNAL_ARTICLE = auto()
    BOOK = auto()
    BOOK_CHAPTER = auto()
    WEBSITE = auto()
    REPORT = auto()
    AI_SOURCE = auto()
    UNKNOWN = auto()


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class Position:
    """A span in the source text (character offsets)."""

    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Author:
    family: str
    given_initials: str = ""  # e.g., "J. K."


@dataclass(frozen=True, slots=True)
class Reference:
    raw: str
    ref_type: ReferenceType
    authors: list[Author]
    year: str
    title: str
    position: Position
    container: str | None = None  # journal name, book title for chapters, site name
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    isbn: str | None = None
    url: str | None = None
    publisher: str | None = None
    extras: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Citation:
    raw: str
    authors: list[str]  # surface form, e.g. ["Smith", "Jones"]
    year: str
    position: Position
    page: str | None = None
    narrative: bool = False
    secondary_source_author: str | None = None  # for "(Brown, 2010, as cited in Smith, 2020)"


@dataclass(frozen=True, slots=True)
class Issue:
    code: str  # stable machine-readable identifier, e.g. "doi_not_found"
    severity: Severity
    message: str
    position: Position
    suggestion: str | None = None
    target_kind: str = "reference"  # "reference" | "citation" | "global"


@dataclass(frozen=True, slots=True)
class Report:
    references: list[Reference]
    citations: list[Citation]
    issues: list[Issue]
    warnings: list[str]
    degraded_checks: list[str]
```

- [ ] **Step 4: Run the test to confirm it passes**

Run: `uv run pytest packages/engine/tests/test_models.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Add the conftest used by later tests**

```python
# packages/engine/tests/conftest.py
"""Shared pytest fixtures for the engine test suite."""

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_path() -> Path:
    return FIXTURE_DIR
```

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/models.py packages/engine/tests/conftest.py packages/engine/tests/test_models.py
git commit -m "feat(engine): add core domain models (Reference, Citation, Issue, Report)"
```

---

### Task 4: Public API surface (stubs)

**Files:**
- Create: `packages/engine/src/apa7_validator/api.py`
- Modify: `packages/engine/src/apa7_validator/__init__.py`
- Create: `packages/engine/tests/test_api_stubs.py`

- [ ] **Step 1: Write the failing test that the public API symbols exist**

```python
# packages/engine/tests/test_api_stubs.py
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
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `uv run pytest packages/engine/tests/test_api_stubs.py -v`
Expected: FAIL — `AttributeError: module 'apa7_validator' has no attribute 'validate'`.

- [ ] **Step 3: Write the API stubs**

```python
# packages/engine/src/apa7_validator/api.py
"""Public API of the validator engine.

The actual implementations are wired in Task 37 (validate) and Task 36
(annotate_docx). This module defines the stable surface area.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .models import Report

if TYPE_CHECKING:
    from .clients.base import Clients

Format = Literal["text", "docx", "pdf"]


def validate(
    source: bytes | str,
    format: Format,
    *,
    clients: Clients | None = None,
) -> Report:
    """Validate an essay's APA 7 references and citations.

    `source` is bytes for DOCX/PDF, str for text. `clients` is an optional
    bundle of lookup clients (CrossRef, Unpaywall, OpenLibrary, URL liveness).
    Pass `None` to use clients in dry-run mode (no network).
    """
    raise NotImplementedError("Wired in Task 37")


def annotate_docx(
    source: bytes | None,
    report: Report,
) -> bytes:
    """Produce an annotated `.docx` from a `Report`.

    If `source` is the original DOCX bytes, comments are injected into a copy
    of that document preserving its formatting. If `source` is None (the input
    was text or PDF), a fresh DOCX is generated from the extracted text and
    comments injected into that.
    """
    raise NotImplementedError("Wired in Task 36")
```

- [ ] **Step 4: Re-export from package root**

```python
# packages/engine/src/apa7_validator/__init__.py
"""APA 7 reference and citation validator."""

from .api import Format, annotate_docx, validate
from .models import (
    Author,
    Citation,
    Issue,
    Position,
    Reference,
    ReferenceType,
    Report,
    Severity,
)

__version__ = "0.1.0"

__all__ = [
    "Author",
    "Citation",
    "Format",
    "Issue",
    "Position",
    "Reference",
    "ReferenceType",
    "Report",
    "Severity",
    "annotate_docx",
    "validate",
]
```

- [ ] **Step 5: Run the test to confirm it passes**

Run: `uv run pytest packages/engine/tests/test_api_stubs.py -v`
Expected: 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/api.py packages/engine/src/apa7_validator/__init__.py packages/engine/tests/test_api_stubs.py
git commit -m "feat(engine): add public API stubs (validate, annotate_docx)"
```

---

### Task 5: Text extractor + extractor base

**Files:**
- Create: `packages/engine/src/apa7_validator/extractors/__init__.py`
- Create: `packages/engine/src/apa7_validator/extractors/base.py`
- Create: `packages/engine/src/apa7_validator/extractors/text.py`
- Create: `packages/engine/tests/extractors/__init__.py`
- Create: `packages/engine/tests/extractors/test_text_extractor.py`

- [ ] **Step 1: Write the failing test for text extraction**

```python
# packages/engine/tests/extractors/test_text_extractor.py
from apa7_validator.extractors.text import TextExtractor


def test_text_extractor_returns_extraction_result():
    extractor = TextExtractor()
    result = extractor.extract("Hello world.")
    assert result.text == "Hello world."
    assert result.position_map.kind == "char_offset"
    assert result.source_kind == "text"


def test_text_extractor_preserves_offsets_via_identity_map():
    extractor = TextExtractor()
    result = extractor.extract("ABCDE")
    # For text input, source offset == extracted offset (identity map)
    assert result.position_map.to_source(2) == ("char_offset", 2)
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `uv run pytest packages/engine/tests/extractors/test_text_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apa7_validator.extractors'`.

- [ ] **Step 3: Create the extractor base types**

```python
# packages/engine/src/apa7_validator/extractors/base.py
"""Common types for all extractors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

PositionKind = Literal["char_offset", "docx_run", "pdf_char_offset"]


@dataclass(frozen=True, slots=True)
class PositionMap:
    """Maps extracted-text offsets back to a source-specific location.

    For now, every extractor uses an identity (char_offset) map. DOCX and PDF
    extractors will extend this with richer maps in Tasks 6 and 7.
    """

    kind: PositionKind

    def to_source(self, extracted_offset: int) -> tuple[PositionKind, int]:
        return (self.kind, extracted_offset)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    position_map: PositionMap
    source_kind: Literal["text", "docx", "pdf"]
    warnings: list[str]


class Extractor(Protocol):
    def extract(self, source: bytes | str) -> ExtractionResult: ...


class ExtractorError(Exception):
    """Base for extractor-level failures (encrypted input, no extractable text)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
```

- [ ] **Step 4: Create the text extractor**

```python
# packages/engine/src/apa7_validator/extractors/text.py
from __future__ import annotations

from .base import ExtractionResult, PositionMap


class TextExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, bytes):
            text = source.decode("utf-8")
        else:
            text = source
        return ExtractionResult(
            text=text,
            position_map=PositionMap(kind="char_offset"),
            source_kind="text",
            warnings=[],
        )
```

- [ ] **Step 5: Add the extractors package init**

```python
# packages/engine/src/apa7_validator/extractors/__init__.py
from .base import ExtractionResult, Extractor, ExtractorError, PositionMap
from .text import TextExtractor

__all__ = [
    "ExtractionResult",
    "Extractor",
    "ExtractorError",
    "PositionMap",
    "TextExtractor",
]
```

- [ ] **Step 6: Run the tests to confirm they pass**

Run: `uv run pytest packages/engine/tests/extractors/test_text_extractor.py -v`
Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add packages/engine/src/apa7_validator/extractors/ packages/engine/tests/extractors/
git commit -m "feat(engine): add extractor base types and text extractor"
```

---

### Task 6: DOCX extractor with rich position map

**Files:**
- Create: `packages/engine/src/apa7_validator/extractors/docx.py`
- Modify: `packages/engine/src/apa7_validator/extractors/base.py` (add `DocxPositionMap`)
- Create: `packages/engine/tests/fixtures/docx/sample_essay.docx` (small synthetic fixture)
- Create: `packages/engine/tests/extractors/test_docx_extractor.py`
- Create: `packages/engine/tests/extractors/_make_fixture_docx.py` (one-shot generator script)

- [ ] **Step 1: Write the helper script that generates the fixture DOCX**

```python
# packages/engine/tests/extractors/_make_fixture_docx.py
"""One-shot generator for tests/fixtures/docx/sample_essay.docx.

Run once via: uv run python -m tests.extractors._make_fixture_docx
The output is committed; this script is here for reproducibility.
"""

from pathlib import Path

from docx import Document

OUT = (
    Path(__file__).parent.parent
    / "fixtures"
    / "docx"
    / "sample_essay.docx"
)


def main() -> None:
    doc = Document()
    doc.add_heading("Body", level=1)
    doc.add_paragraph(
        "Climate change is well documented (Smith, 2020). Recent work "
        "extends this (Jones & Lee, 2021)."
    )
    doc.add_heading("References", level=1)
    doc.add_paragraph(
        "Jones, A., & Lee, B. (2021). New analyses of climate data. "
        "Climate Journal, 5(2), 100-120. https://doi.org/10.1234/cj.2021.05"
    )
    doc.add_paragraph(
        "Smith, J. (2020). Foundations of climate research. "
        "Earth Press."
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate and commit the fixture**

Run:
```bash
cd "packages/engine"
uv run python -m tests.extractors._make_fixture_docx
cd ../..
git add packages/engine/tests/extractors/_make_fixture_docx.py packages/engine/tests/fixtures/docx/sample_essay.docx
```
Expected: prints `wrote .../sample_essay.docx`; file appears under `packages/engine/tests/fixtures/docx/`.

- [ ] **Step 3: Write the failing test for the DOCX extractor**

```python
# packages/engine/tests/extractors/test_docx_extractor.py
from pathlib import Path

import pytest

from apa7_validator.extractors.docx import DocxExtractor


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_docx_extractor_returns_concatenated_text(sample_docx: bytes):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    assert "Climate change is well documented" in result.text
    assert "Smith, J. (2020). Foundations of climate research." in result.text
    assert result.source_kind == "docx"


def test_docx_extractor_position_map_maps_offset_to_paragraph_index(
    sample_docx: bytes,
):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    body_idx = result.text.index("Climate change")
    kind, ref = result.position_map.to_source(body_idx)
    assert kind == "docx_run"
    # ref is a (paragraph_index, run_index, offset_in_run) tuple
    assert isinstance(ref, tuple) and len(ref) == 3


def test_docx_extractor_raises_on_encrypted_input():
    from apa7_validator.extractors.base import ExtractorError

    extractor = DocxExtractor()
    # An encrypted DOCX would normally come from Word's password-protect.
    # python-docx raises on opening such files; we re-raise as ExtractorError.
    with pytest.raises(ExtractorError) as excinfo:
        extractor.extract(b"not a docx at all")
    assert excinfo.value.code in {"encrypted_input", "invalid_docx"}
```

- [ ] **Step 4: Run the tests to confirm they fail**

Run: `uv run pytest packages/engine/tests/extractors/test_docx_extractor.py -v`
Expected: 3 FAILs with `ModuleNotFoundError` / `ImportError` on `DocxExtractor`.

- [ ] **Step 5: Extend `base.py` with a richer position map type**

Update `packages/engine/src/apa7_validator/extractors/base.py`:

```python
# packages/engine/src/apa7_validator/extractors/base.py
"""Common types for all extractors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

PositionKind = Literal["char_offset", "docx_run", "pdf_char_offset"]


@dataclass(frozen=True, slots=True)
class PositionMap:
    """Maps extracted-text offsets back to a source-specific location.

    `entries` is a sorted list of (extracted_offset, source_ref) tuples. For
    `kind="char_offset"` the entries list is empty (identity). For `kind="docx_run"`
    each entry's source_ref is (paragraph_index, run_index, offset_in_run). For
    `kind="pdf_char_offset"` each entry's source_ref is (page_index, char_offset).
    """

    kind: PositionKind
    entries: list[tuple[int, Any]] = field(default_factory=list)

    def to_source(self, extracted_offset: int) -> tuple[PositionKind, Any]:
        if self.kind == "char_offset":
            return ("char_offset", extracted_offset)
        # Find the last entry whose offset <= extracted_offset.
        lo, hi = 0, len(self.entries) - 1
        best = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.entries[mid][0] <= extracted_offset:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return (self.kind, self.entries[best][1])


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    position_map: PositionMap
    source_kind: Literal["text", "docx", "pdf"]
    warnings: list[str]


class Extractor(Protocol):
    def extract(self, source: bytes | str) -> ExtractionResult: ...


class ExtractorError(Exception):
    """Base for extractor-level failures (encrypted input, no extractable text)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
```

- [ ] **Step 6: Implement the DOCX extractor**

```python
# packages/engine/src/apa7_validator/extractors/docx.py
from __future__ import annotations

import io
from typing import Any

import docx
from docx.opc.exceptions import PackageNotFoundError

from .base import ExtractionResult, ExtractorError, PositionMap


class DocxExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, str):
            raise ExtractorError(
                "invalid_input",
                "DocxExtractor requires bytes, got str",
            )
        try:
            document = docx.Document(io.BytesIO(source))
        except PackageNotFoundError as exc:
            raise ExtractorError(
                "invalid_docx",
                f"Not a valid DOCX file: {exc}",
            ) from exc
        except Exception as exc:
            if "encrypted" in str(exc).lower() or "password" in str(exc).lower():
                raise ExtractorError(
                    "encrypted_input",
                    "DOCX is password-protected",
                ) from exc
            raise ExtractorError("invalid_docx", str(exc)) from exc

        text_parts: list[str] = []
        entries: list[tuple[int, Any]] = []
        cursor = 0
        for p_idx, para in enumerate(document.paragraphs):
            for r_idx, run in enumerate(para.runs):
                if not run.text:
                    continue
                entries.append((cursor, (p_idx, r_idx, 0)))
                text_parts.append(run.text)
                cursor += len(run.text)
            text_parts.append("\n")
            cursor += 1

        return ExtractionResult(
            text="".join(text_parts),
            position_map=PositionMap(kind="docx_run", entries=entries),
            source_kind="docx",
            warnings=[],
        )
```

- [ ] **Step 7: Re-export the DOCX extractor**

Update `packages/engine/src/apa7_validator/extractors/__init__.py`:

```python
from .base import ExtractionResult, Extractor, ExtractorError, PositionMap
from .docx import DocxExtractor
from .text import TextExtractor

__all__ = [
    "DocxExtractor",
    "ExtractionResult",
    "Extractor",
    "ExtractorError",
    "PositionMap",
    "TextExtractor",
]
```

- [ ] **Step 8: Run the tests to confirm they pass**

Run: `uv run pytest packages/engine/tests/extractors/test_docx_extractor.py -v`
Expected: 3 tests pass.

- [ ] **Step 9: Commit**

```bash
git add packages/engine/src/apa7_validator/extractors/ packages/engine/tests/extractors/ packages/engine/tests/fixtures/docx/
git commit -m "feat(engine): add DOCX extractor with paragraph/run position map"
```

---

### Task 7: PDF extractor (text-extractable PDFs only)

**Files:**
- Create: `packages/engine/src/apa7_validator/extractors/pdf.py`
- Create: `packages/engine/tests/fixtures/pdf/sample_essay.pdf` (one-shot generated)
- Create: `packages/engine/tests/extractors/_make_fixture_pdf.py`
- Create: `packages/engine/tests/extractors/test_pdf_extractor.py`

- [ ] **Step 1: Write the helper script that generates the fixture PDF**

```python
# packages/engine/tests/extractors/_make_fixture_pdf.py
"""One-shot generator for tests/fixtures/pdf/sample_essay.pdf.

Run via: uv run python -m tests.extractors._make_fixture_pdf
"""

from pathlib import Path

import pymupdf

OUT = (
    Path(__file__).parent.parent
    / "fixtures"
    / "pdf"
    / "sample_essay.pdf"
)


def main() -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Climate change is well documented (Smith, 2020).\n"
        "Recent work extends this (Jones & Lee, 2021).\n\n"
        "References\n"
        "Jones, A., & Lee, B. (2021). New analyses of climate data.\n"
        "    Climate Journal, 5(2), 100-120.\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press.\n",
        fontsize=11,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate the fixture**

Run:
```bash
cd "packages/engine"
uv run python -m tests.extractors._make_fixture_pdf
cd ../..
```

- [ ] **Step 3: Write the failing tests**

```python
# packages/engine/tests/extractors/test_pdf_extractor.py
from pathlib import Path

import pytest

from apa7_validator.extractors.base import ExtractorError
from apa7_validator.extractors.pdf import PdfExtractor


@pytest.fixture
def sample_pdf(fixture_path: Path) -> bytes:
    return (fixture_path / "pdf" / "sample_essay.pdf").read_bytes()


def test_pdf_extractor_returns_extracted_text(sample_pdf: bytes):
    extractor = PdfExtractor()
    result = extractor.extract(sample_pdf)
    assert "Climate change is well documented" in result.text
    assert result.source_kind == "pdf"


def test_pdf_extractor_position_map_records_page(sample_pdf: bytes):
    extractor = PdfExtractor()
    result = extractor.extract(sample_pdf)
    idx = result.text.index("Climate change")
    kind, ref = result.position_map.to_source(idx)
    assert kind == "pdf_char_offset"
    page_idx, char_offset = ref
    assert page_idx == 0
    assert isinstance(char_offset, int)


def test_pdf_extractor_flags_scanned_pdf_with_no_text():
    # A blank PDF with no text simulates a scanned image.
    import pymupdf

    doc = pymupdf.open()
    doc.new_page()
    blank_bytes = doc.tobytes()
    extractor = PdfExtractor()
    with pytest.raises(ExtractorError) as excinfo:
        extractor.extract(blank_bytes)
    assert excinfo.value.code == "no_extractable_text"
```

- [ ] **Step 4: Run the tests to confirm they fail**

Run: `uv run pytest packages/engine/tests/extractors/test_pdf_extractor.py -v`
Expected: 3 FAILs with import error on `PdfExtractor`.

- [ ] **Step 5: Implement the PDF extractor**

```python
# packages/engine/src/apa7_validator/extractors/pdf.py
from __future__ import annotations

import io
from typing import Any

import pymupdf

from .base import ExtractionResult, ExtractorError, PositionMap


class PdfExtractor:
    def extract(self, source: bytes | str) -> ExtractionResult:
        if isinstance(source, str):
            raise ExtractorError(
                "invalid_input",
                "PdfExtractor requires bytes, got str",
            )
        try:
            doc = pymupdf.open(stream=io.BytesIO(source), filetype="pdf")
        except Exception as exc:
            raise ExtractorError("invalid_pdf", str(exc)) from exc

        if doc.needs_pass:
            raise ExtractorError("encrypted_input", "PDF is password-protected")

        text_parts: list[str] = []
        entries: list[tuple[int, Any]] = []
        cursor = 0
        for page_idx, page in enumerate(doc):
            page_text = page.get_text("text")  # type: ignore[no-untyped-call]
            if page_text:
                entries.append((cursor, (page_idx, 0)))
                text_parts.append(page_text)
                cursor += len(page_text)
            if page_idx < len(doc) - 1:
                text_parts.append("\n")
                cursor += 1

        full_text = "".join(text_parts)
        if not full_text.strip():
            raise ExtractorError(
                "no_extractable_text",
                "PDF has no extractable text (likely scanned); OCR required",
            )

        return ExtractionResult(
            text=full_text,
            position_map=PositionMap(kind="pdf_char_offset", entries=entries),
            source_kind="pdf",
            warnings=[],
        )
```

- [ ] **Step 6: Re-export the PDF extractor**

Update `packages/engine/src/apa7_validator/extractors/__init__.py`:

```python
from .base import ExtractionResult, Extractor, ExtractorError, PositionMap
from .docx import DocxExtractor
from .pdf import PdfExtractor
from .text import TextExtractor

__all__ = [
    "DocxExtractor",
    "ExtractionResult",
    "Extractor",
    "ExtractorError",
    "PdfExtractor",
    "PositionMap",
    "TextExtractor",
]
```

- [ ] **Step 7: Run the tests to confirm they pass**

Run: `uv run pytest packages/engine/tests/extractors/test_pdf_extractor.py -v`
Expected: 3 tests pass.

- [ ] **Step 8: Commit**

```bash
git add packages/engine/src/apa7_validator/extractors/ packages/engine/tests/extractors/ packages/engine/tests/fixtures/pdf/
git commit -m "feat(engine): add PDF extractor with scanned-PDF detection"
```

---

### Task 8: Reference list splitter

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/__init__.py`
- Create: `packages/engine/src/apa7_validator/parser/reference_list.py`
- Create: `packages/engine/tests/parser/__init__.py`
- Create: `packages/engine/tests/parser/test_reference_list.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_reference_list.py
from apa7_validator.parser.reference_list import split_body_and_references


def test_splits_on_standard_references_heading():
    text = "Body text here.\n\nReferences\n\nSmith, J. (2020). A paper. Journal."
    body, refs_section, found = split_body_and_references(text)
    assert "Body text here." in body
    assert "Smith, J. (2020)" in refs_section
    assert found is True


def test_splits_on_bibliography_heading():
    text = "Body.\n\nBibliography\n\nSmith, J. (2020)."
    body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs


def test_returns_full_text_when_no_heading_found():
    text = "Body only, no references heading."
    body, refs, found = split_body_and_references(text)
    assert body == text
    assert refs == ""
    assert found is False


def test_heading_match_is_case_insensitive_and_line_anchored():
    text = "Body mentions references casually.\n\nREFERENCES\n\nSmith, J."
    body, refs, found = split_body_and_references(text)
    assert found is True
    assert "Smith" in refs
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_reference_list.py -v`
Expected: 4 FAILs on `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/__init__.py
from .reference_list import split_body_and_references

__all__ = ["split_body_and_references"]
```

```python
# packages/engine/src/apa7_validator/parser/reference_list.py
from __future__ import annotations

import re

_HEADING_RE = re.compile(
    r"^[ \t]*(references|reference list|bibliography|works cited)[ \t]*:?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def split_body_and_references(text: str) -> tuple[str, str, bool]:
    """Return (body, references_section, found).

    Splits on the first line that is purely a recognised heading. If no heading
    is found, returns the full text as the body and an empty references section.
    """
    match = _HEADING_RE.search(text)
    if not match:
        return text, "", False
    body = text[: match.start()].rstrip()
    refs = text[match.end() :].lstrip("\n")
    return body, refs, True
```

```python
# packages/engine/tests/parser/__init__.py
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/parser/test_reference_list.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): split body and reference list on heading"
```

---

### Task 9: Reference parser scaffolding + journal article

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/references.py`
- Create: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Create: `packages/engine/src/apa7_validator/parser/ref_types/journal.py`
- Create: `packages/engine/tests/parser/test_references_scaffolding.py`
- Create: `packages/engine/tests/parser/test_journal_parser.py`

- [ ] **Step 1: Write failing scaffolding tests**

```python
# packages/engine/tests/parser/test_references_scaffolding.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.references import parse_references


def test_returns_empty_list_for_empty_section():
    refs = parse_references("", body_offset=0)
    assert refs == []


def test_splits_on_blank_lines_between_entries():
    section = (
        "Smith, J. (2020). A paper. Journal of Things, 1(2), 3-4.\n\n"
        "Jones, A. (2021). Another paper. Journal of Things, 2(3), 4-5."
    )
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 2


def test_unparseable_entry_returned_with_unknown_type():
    section = "This is not a reference at all."
    refs = parse_references(section, body_offset=0)
    assert len(refs) == 1
    assert refs[0].ref_type is ReferenceType.UNKNOWN
```

- [ ] **Step 2: Write failing journal parser tests**

```python
# packages/engine/tests/parser/test_journal_parser.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.journal import try_parse_journal


def test_parses_basic_journal_reference():
    raw = (
        "Smith, J. K. (2020). The effects of A on B. "
        "Journal of Things, 5(2), 100-120. https://doi.org/10.1234/jot.2020.05"
    )
    ref = try_parse_journal(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.JOURNAL_ARTICLE
    assert ref.authors[0].family == "Smith"
    assert ref.authors[0].given_initials == "J. K."
    assert ref.year == "2020"
    assert ref.title == "The effects of A on B"
    assert ref.container == "Journal of Things"
    assert ref.volume == "5"
    assert ref.issue == "2"
    assert ref.pages == "100-120"
    assert ref.doi == "10.1234/jot.2020.05"


def test_parses_journal_with_two_authors_and_no_doi():
    raw = "Smith, J., & Jones, A. (2019). A study. Nature Reviews, 12, 5-7."
    ref = try_parse_journal(raw, position_start=0)
    assert ref is not None
    assert [a.family for a in ref.authors] == ["Smith", "Jones"]
    assert ref.year == "2019"
    assert ref.doi is None


def test_returns_none_for_clearly_non_journal():
    raw = "Smith, J. (2020). A book. Earth Press."
    # No volume/issue/pages — not a journal article.
    ref = try_parse_journal(raw, position_start=0)
    assert ref is None
```

- [ ] **Step 3: Run to confirm failures**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: import errors / fails on `parse_references` and `try_parse_journal`.

- [ ] **Step 4: Implement the ref_types package init**

```python
# packages/engine/src/apa7_validator/parser/ref_types/__init__.py
from .journal import try_parse_journal

__all__ = ["try_parse_journal"]
```

- [ ] **Step 5: Implement the journal article parser**

```python
# packages/engine/src/apa7_validator/parser/ref_types/journal.py
from __future__ import annotations

import re

from apa7_validator.models import Author, Position, Reference, ReferenceType

# Journal article shape (loose):
#   <authors> (<year>). <title>. <Journal>, <volume>(<issue>), <pages>. [doi/url]
_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?P<container>[A-Z][^,]+),\s*
    (?P<volume>\d+)
    (?:\((?P<issue>[^)]+)\))?
    (?:,\s*(?P<pages>[\d\-–,\s]+))?
    \.?\s*
    (?:https?://(?:dx\.)?doi\.org/(?P<doi>\S+))?
    """,
    re.VERBOSE,
)


def _parse_authors(raw: str) -> list[Author]:
    # Split on ", &" or "&" first, then take everything before as comma-separated
    # "Last, F. M." groups. APA author lists are: "Smith, J., Jones, A., & Lee, B."
    # We split conservatively by ", " and stitch family/initials.
    parts = [p.strip().rstrip(",") for p in re.split(r",\s*&\s*|,\s+", raw) if p.strip()]
    authors: list[Author] = []
    i = 0
    while i < len(parts):
        family = parts[i]
        initials = parts[i + 1] if i + 1 < len(parts) and re.match(r"^[A-Z]\.", parts[i + 1]) else ""
        authors.append(Author(family=family, given_initials=initials))
        i += 2 if initials else 1
    return authors


def try_parse_journal(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        container=m.group("container").strip(),
        volume=m.group("volume"),
        issue=m.group("issue"),
        pages=m.group("pages").strip() if m.group("pages") else None,
        doi=m.group("doi"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 6: Implement the dispatcher**

```python
# packages/engine/src/apa7_validator/parser/references.py
from __future__ import annotations

import re

from apa7_validator.models import Author, Position, Reference, ReferenceType

from .ref_types import try_parse_journal


def parse_references(section: str, body_offset: int) -> list[Reference]:
    """Split a references section into entries and parse each into a `Reference`.

    Entries are separated by blank lines OR by a newline followed by a line
    that starts with a capital letter (heuristic: each new APA reference
    begins with an author surname). For now, blank-line splitting is enough.
    """
    if not section.strip():
        return []

    raw_entries = [chunk.strip() for chunk in re.split(r"\n\s*\n", section) if chunk.strip()]
    refs: list[Reference] = []
    cursor = body_offset
    for entry in raw_entries:
        # Find absolute position within original text.
        start = section.find(entry) + body_offset if section.find(entry) >= 0 else cursor
        parsed = _try_parse_any(entry, start)
        if parsed is None:
            parsed = Reference(
                raw=entry,
                ref_type=ReferenceType.UNKNOWN,
                authors=[Author(family="?", given_initials="")],
                year="",
                title="",
                position=Position(start=start, end=start + len(entry)),
            )
        refs.append(parsed)
        cursor = start + len(entry)
    return refs


def _try_parse_any(raw: str, position_start: int) -> Reference | None:
    # Order matters: more specific parsers first. Tasks 10-14 extend this.
    for fn in (try_parse_journal,):
        ref = fn(raw, position_start)
        if ref is not None:
            return ref
    return None
```

- [ ] **Step 7: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: scaffolding + journal tests pass.

- [ ] **Step 8: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add reference parser scaffolding and journal article parser"
```

---

### Task 10: Book reference parser

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/ref_types/book.py`
- Modify: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Modify: `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any` (add book to chain)
- Create: `packages/engine/tests/parser/test_book_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_book_parser.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.book import try_parse_book


def test_parses_basic_book():
    raw = "Smith, J. (2020). Foundations of climate research. Earth Press."
    ref = try_parse_book(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.BOOK
    assert ref.authors[0].family == "Smith"
    assert ref.year == "2020"
    assert ref.title == "Foundations of climate research"
    assert ref.publisher == "Earth Press"


def test_parses_book_with_doi():
    raw = (
        "Brown, K. (2018). Statistical methods. "
        "Academic Press. https://doi.org/10.5555/spm.2018"
    )
    ref = try_parse_book(raw, position_start=0)
    assert ref is not None
    assert ref.doi == "10.5555/spm.2018"
    assert ref.publisher == "Academic Press"


def test_rejects_journal_shape():
    raw = "Smith, J. (2020). A paper. Journal, 5(2), 100-120."
    ref = try_parse_book(raw, position_start=0)
    assert ref is None
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_book_parser.py -v`
Expected: import error.

- [ ] **Step 3: Implement the book parser**

```python
# packages/engine/src/apa7_validator/parser/ref_types/book.py
from __future__ import annotations

import re

from apa7_validator.models import Position, Reference, ReferenceType

from .journal import _parse_authors  # reuse author parsing

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?P<publisher>[A-Z][^.]+?)\.?\s*
    (?:https?://(?:dx\.)?doi\.org/(?P<doi>\S+))?\s*$
    """,
    re.VERBOSE,
)

_JOURNAL_TAIL = re.compile(r",\s*\d+(\([^)]+\))?,\s*[\d\-–]+")


def try_parse_book(raw: str, position_start: int) -> Reference | None:
    if _JOURNAL_TAIL.search(raw):
        return None
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        publisher=m.group("publisher").strip(),
        doi=m.group("doi"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 4: Add book to the dispatch chain**

Update `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`:

```python
from .book import try_parse_book
from .journal import try_parse_journal

__all__ = ["try_parse_book", "try_parse_journal"]
```

Update `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any`:

```python
from .ref_types import try_parse_book, try_parse_journal


def _try_parse_any(raw: str, position_start: int) -> Reference | None:
    for fn in (try_parse_journal, try_parse_book):
        ref = fn(raw, position_start)
        if ref is not None:
            return ref
    return None
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: all parser tests pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add book reference parser"
```

---

### Task 11: Book chapter parser

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/ref_types/book_chapter.py`
- Modify: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Modify: `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any`
- Create: `packages/engine/tests/parser/test_book_chapter_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_book_chapter_parser.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.book_chapter import try_parse_book_chapter


def test_parses_book_chapter_with_editor_marker():
    raw = (
        "Smith, J. (2020). A chapter title. In K. Editor (Ed.), "
        "Book title (pp. 100-120). Earth Press."
    )
    ref = try_parse_book_chapter(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.BOOK_CHAPTER
    assert ref.authors[0].family == "Smith"
    assert ref.title == "A chapter title"
    assert ref.container == "Book title"
    assert ref.pages == "100-120"
    assert ref.publisher == "Earth Press"


def test_rejects_journal_shape():
    raw = "Smith, J. (2020). A paper. Journal, 5(2), 100-120."
    assert try_parse_book_chapter(raw, position_start=0) is None
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_book_chapter_parser.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/ref_types/book_chapter.py
from __future__ import annotations

import re

from apa7_validator.models import Position, Reference, ReferenceType

from .journal import _parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.]+?)\.\s*
    In\s+(?P<editors>[^()]+?)\s*\((Eds?\.)\),\s*
    (?P<container>[^()]+?)\s*
    \(pp\.\s*(?P<pages>[\d\-–]+)\)\.\s*
    (?P<publisher>[A-Z][^.]+?)\.?\s*$
    """,
    re.VERBOSE,
)


def try_parse_book_chapter(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.BOOK_CHAPTER,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        container=m.group("container").strip(),
        pages=m.group("pages").strip(),
        publisher=m.group("publisher").strip(),
        extras={"editors": m.group("editors").strip()},
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 4: Wire into dispatch chain**

Update `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`:

```python
from .book import try_parse_book
from .book_chapter import try_parse_book_chapter
from .journal import try_parse_journal

__all__ = ["try_parse_book", "try_parse_book_chapter", "try_parse_journal"]
```

Update `_try_parse_any` in `references.py` to: `(try_parse_journal, try_parse_book_chapter, try_parse_book)`. Book chapter must come before book because book is the looser match.

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: all parser tests pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add book chapter reference parser"
```

---

### Task 12: Website / webpage parser

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/ref_types/website.py`
- Modify: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Modify: `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any`
- Create: `packages/engine/tests/parser/test_website_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_website_parser.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.website import try_parse_website


def test_parses_basic_webpage_with_n_d():
    raw = (
        "World Health Organization. (n.d.). Climate change and health. "
        "WHO. https://www.who.int/climate"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.ref_type is ReferenceType.WEBSITE
    assert ref.year == "n.d."
    assert ref.title == "Climate change and health"
    assert ref.url == "https://www.who.int/climate"
    assert ref.container == "WHO"


def test_parses_webpage_with_date():
    raw = (
        "Doe, J. (2022, March 5). A web article. Some Site. "
        "https://example.com/post"
    )
    ref = try_parse_website(raw, position_start=0)
    assert ref is not None
    assert ref.year == "2022"
    assert ref.url == "https://example.com/post"
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_website_parser.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/ref_types/website.py
from __future__ import annotations

import re

from apa7_validator.models import Position, Reference, ReferenceType

from .journal import _parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>n\.d\.|\d{4})(?:,\s*[^)]+)?\)\.\s*
    (?P<title>[^.]+?)\.\s*
    (?P<container>[A-Z][^.]+?)\.\s*
    (?P<url>https?://\S+)\s*$
    """,
    re.VERBOSE,
)


def try_parse_website(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.WEBSITE,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        container=m.group("container").strip(),
        url=m.group("url"),
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 4: Wire into dispatch chain**

Update `_try_parse_any` in `references.py` to include `try_parse_website` after `try_parse_book_chapter` and before `try_parse_book`. Update `ref_types/__init__.py` to export.

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add website/webpage reference parser"
```

---

### Task 13: Report parser

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/ref_types/report.py`
- Modify: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Modify: `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any`
- Create: `packages/engine/tests/parser/test_report_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_report_parser.py
from apa7_validator.models import ReferenceType
from apa7_validator.parser.ref_types.report import try_parse_report


def test_parses_government_report_with_number():
    raw = (
        "Australian Bureau of Statistics. (2023). Population trends "
        "(Report No. 3101.0). ABS."
    )
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
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_report_parser.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/ref_types/report.py
from __future__ import annotations

import re

from apa7_validator.models import Position, Reference, ReferenceType

from .journal import _parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^.()]+?)\s*
    (?:\(Report\s+No\.\s*(?P<report_no>[^)]+)\)\.?\s*)?
    (?P<publisher>[A-Z][^.]+?)\.?\s*
    (?:https?://(?:dx\.)?doi\.org/(?P<doi>\S+))?\s*$
    """,
    re.VERBOSE,
)

_REPORT_HINT = re.compile(r"report|bureau|department|OECD|UN|WHO", re.IGNORECASE)


def try_parse_report(raw: str, position_start: int) -> Reference | None:
    if not _REPORT_HINT.search(raw):
        return None
    m = _RE.match(raw.strip())
    if not m:
        return None
    extras: dict[str, str] = {}
    if m.group("report_no"):
        extras["report_number"] = m.group("report_no").strip()
    return Reference(
        raw=raw,
        ref_type=ReferenceType.REPORT,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        publisher=m.group("publisher").strip(),
        doi=m.group("doi"),
        extras=extras,
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 4: Wire into dispatch chain**

`_try_parse_any` order: `(try_parse_journal, try_parse_book_chapter, try_parse_website, try_parse_report, try_parse_book)`. Update `ref_types/__init__.py`.

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add report reference parser"
```

---

### Task 14: AI source parser (ChatGPT et al.)

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/ref_types/ai_source.py`
- Modify: `packages/engine/src/apa7_validator/parser/ref_types/__init__.py`
- Modify: `packages/engine/src/apa7_validator/parser/references.py:_try_parse_any`
- Create: `packages/engine/tests/parser/test_ai_source_parser.py`

- [ ] **Step 1: Write failing tests**

APA 7's guidance (per APA Style Blog, 2023) for ChatGPT: `OpenAI. (2023). ChatGPT (Mar 14 version) [Large language model]. https://chat.openai.com/chat`.

```python
# packages/engine/tests/parser/test_ai_source_parser.py
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
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_ai_source_parser.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/ref_types/ai_source.py
from __future__ import annotations

import re

from apa7_validator.models import Position, Reference, ReferenceType

from .journal import _parse_authors

_RE = re.compile(
    r"""
    ^(?P<authors>.+?)\s*
    \((?P<year>\d{4}[a-z]?)\)\.\s*
    (?P<title>[^[]+?)\s*
    \[(?P<model_kind>[^\]]+)\]\.\s*
    (?P<url>https?://\S+)\s*$
    """,
    re.VERBOSE,
)

_MODEL_KIND_HINT = re.compile(
    r"large language model|generative ai|ai model|gpt|llm",
    re.IGNORECASE,
)


def try_parse_ai_source(raw: str, position_start: int) -> Reference | None:
    m = _RE.match(raw.strip())
    if not m:
        return None
    if not _MODEL_KIND_HINT.search(m.group("model_kind")):
        return None
    return Reference(
        raw=raw,
        ref_type=ReferenceType.AI_SOURCE,
        authors=_parse_authors(m.group("authors")),
        year=m.group("year"),
        title=m.group("title").strip(),
        url=m.group("url"),
        extras={"model_kind": m.group("model_kind").strip()},
        position=Position(start=position_start, end=position_start + len(raw)),
    )
```

- [ ] **Step 4: Wire in**

`_try_parse_any` order: `(try_parse_ai_source, try_parse_journal, try_parse_book_chapter, try_parse_website, try_parse_report, try_parse_book)`. AI source first because `[Large language model]` bracket is a unique anchor. Update `ref_types/__init__.py`.

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add AI source reference parser (ChatGPT and similar)"
```

---

### Task 15: In-text citation parser

**Files:**
- Create: `packages/engine/src/apa7_validator/parser/citations.py`
- Modify: `packages/engine/src/apa7_validator/parser/__init__.py` (export `parse_citations`)
- Create: `packages/engine/tests/parser/test_citations.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/parser/test_citations.py
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
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/parser/test_citations.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/parser/citations.py
from __future__ import annotations

import re

from apa7_validator.models import Citation, Position

# Parenthetical: (Author, YYYY) or (Author et al., YYYY) or (A & B, YYYY)
#   optional ", p. N" / ", pp. N-M"
#   optional "as cited in OtherAuthor, YYYY"
_PAREN_RE = re.compile(
    r"""
    \(
    (?P<authors>[^(),]+?(?:\s*&\s*[^(),]+?)?(?:\s+et\s+al\.)?)
    ,\s*
    (?:
        (?P<sec_year>\d{4}[a-z]?)
        ,\s*as\s+cited\s+in\s+
        (?P<cited_author>[^,)]+?)
        ,\s*(?P<cited_year>\d{4}[a-z]?)
    |
        (?P<year>\d{4}[a-z]?)
        (?:,\s*pp?\.\s*(?P<page>[\d\-–]+))?
    )
    \)
    """,
    re.VERBOSE,
)

# Narrative: Smith (2020) or Smith and Jones (2020) or Smith et al. (2020)
_NARRATIVE_RE = re.compile(
    r"""
    \b
    (?P<authors>[A-Z][a-zA-Z\-']+(?:\s+(?:and|&)\s+[A-Z][a-zA-Z\-']+)?(?:\s+et\s+al\.)?)
    \s+
    \(
    (?P<year>\d{4}[a-z]?)
    (?:,\s*pp?\.\s*(?P<page>[\d\-–]+))?
    \)
    """,
    re.VERBOSE,
)


def _split_authors(raw: str) -> list[str]:
    raw = raw.strip()
    if "et al." in raw:
        return [raw]
    parts = re.split(r"\s*(?:&|and)\s*", raw)
    return [p.strip() for p in parts if p.strip()]


def parse_citations(text: str) -> list[Citation]:
    cits: list[Citation] = []

    for m in _PAREN_RE.finditer(text):
        if m.group("cited_author") is not None:
            cits.append(
                Citation(
                    raw=m.group(0),
                    authors=[m.group("cited_author").strip()],
                    year=m.group("cited_year"),
                    page=None,
                    narrative=False,
                    secondary_source_author=_split_authors(m.group("authors"))[0],
                    position=Position(start=m.start(), end=m.end()),
                )
            )
        else:
            cits.append(
                Citation(
                    raw=m.group(0),
                    authors=_split_authors(m.group("authors")),
                    year=m.group("year"),
                    page=m.group("page"),
                    narrative=False,
                    position=Position(start=m.start(), end=m.end()),
                )
            )

    for m in _NARRATIVE_RE.finditer(text):
        # Avoid double-counting if the parenthetical regex already matched the same span.
        if any(c.position.start <= m.start() < c.position.end for c in cits):
            continue
        cits.append(
            Citation(
                raw=m.group(0),
                authors=_split_authors(m.group("authors")),
                year=m.group("year"),
                page=m.group("page"),
                narrative=True,
                position=Position(start=m.start(), end=m.end()),
            )
        )

    cits.sort(key=lambda c: c.position.start)
    return cits
```

- [ ] **Step 4: Export from parser package**

Update `packages/engine/src/apa7_validator/parser/__init__.py`:

```python
from .citations import parse_citations
from .reference_list import split_body_and_references
from .references import parse_references

__all__ = ["parse_citations", "parse_references", "split_body_and_references"]
```

- [ ] **Step 5: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/parser/ -v`
Expected: 7 citation tests pass plus all prior parser tests still green.

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/parser/ packages/engine/tests/parser/
git commit -m "feat(engine): add in-text citation parser (parenthetical, narrative, secondary)"
```

---

**End of Phase A.** At this point `apa7_validator.parser.parse_references()` returns structured `Reference` objects from a references section, `apa7_validator.parser.parse_citations()` extracts in-text citations from body text, and all three extractors (`Text`, `Docx`, `Pdf`) yield `ExtractionResult`s with position maps. Worth pausing here to run the full suite, eyeball the parser outputs against real APA 7 manual examples, and commit any quick fixes before Phase B.

Suggested checkpoint command:

```bash
uv run pytest packages/engine/tests -v
uv run ruff check .
uv run pyright packages/engine/src
```

---

# Phase B — Validation (Tasks 16–32)

End state: `apa7_validator.api.validate(...)` (internal call path, not yet wired through the public API) produces a complete `Report` containing formatting issues, cross-matching issues, and existence-check issues, with network-aware degradation.

---

### Task 16: Validator framework

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/__init__.py`
- Create: `packages/engine/src/apa7_validator/validators/base.py`
- Create: `packages/engine/tests/validators/__init__.py`
- Create: `packages/engine/tests/validators/test_base.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/test_base.py
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
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/validators/test_base.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/validators/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from apa7_validator.models import Issue, Position, Reference, Severity


@dataclass(frozen=True, slots=True)
class IssueBuilder:
    target_kind: str  # "reference" | "citation" | "global"

    def error(
        self, code: str, message: str, position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code, severity=Severity.ERROR, message=message,
            position=position, suggestion=suggestion, target_kind=self.target_kind,
        )

    def warning(
        self, code: str, message: str, position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code, severity=Severity.WARNING, message=message,
            position=position, suggestion=suggestion, target_kind=self.target_kind,
        )

    def info(
        self, code: str, message: str, position: Position,
        suggestion: str | None = None,
    ) -> Issue:
        return Issue(
            code=code, severity=Severity.INFO, message=message,
            position=position, suggestion=suggestion, target_kind=self.target_kind,
        )


class Rule(Protocol):
    def __call__(self, ref: Reference) -> list[Issue]: ...
```

```python
# packages/engine/src/apa7_validator/validators/__init__.py
from .base import IssueBuilder, Rule

__all__ = ["IssueBuilder", "Rule"]
```

```python
# packages/engine/tests/validators/__init__.py
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/validators/test_base.py -v`
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/engine/src/apa7_validator/validators/ packages/engine/tests/validators/
git commit -m "feat(engine): add validator framework (IssueBuilder, Rule protocol)"
```

---

### Task 17: Cross-cutting formatting rules

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/__init__.py`
- Create: `packages/engine/src/apa7_validator/validators/formatting/cross_cutting.py`
- Create: `packages/engine/tests/validators/formatting/__init__.py`
- Create: `packages/engine/tests/validators/formatting/test_cross_cutting.py`

Cross-cutting APA 7 rules covered in this task:

- `R-CC-1`: Reference list is alphabetised by first author's family name.
- `R-CC-2`: Author list with 21+ authors uses `…` ellipsis before the last author; otherwise list every author.
- `R-CC-3`: DOI strings start with `10.` (not `doi:`, not `http`); the surface form in a reference must be `https://doi.org/<doi>`.
- `R-CC-4`: Year is exactly four digits, or `n.d.`, optionally suffixed with a single lowercase letter (`2020a`).
- `R-CC-5`: Title sentence case (first word capitalised, proper nouns capitalised; rest lowercase).

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/formatting/test_cross_cutting.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.cross_cutting import (
    check_alphabetical_order,
    check_doi_format,
    check_title_sentence_case,
    check_year_format,
)


def _ref(family: str, year: str = "2020", title: str = "A paper", doi: str | None = None) -> Reference:
    return Reference(
        raw="x", ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year=year, title=title, doi=doi,
        position=Position(0, 1),
    )


def test_alphabetical_order_flags_misordered_pair():
    refs = [_ref("Smith"), _ref("Jones")]
    issues = check_alphabetical_order(refs)
    assert any(i.code == "references_not_alphabetised" for i in issues)


def test_alphabetical_order_clean_when_sorted():
    refs = [_ref("Jones"), _ref("Smith")]
    assert check_alphabetical_order(refs) == []


def test_doi_format_flags_http_prefix_only():
    ref = _ref("Smith", doi="10.1234/abc")
    assert check_doi_format(ref) == []


def test_doi_format_flags_bare_doi_word_prefix():
    # Parser strips the URL; if a parser leaves "doi:" in, that's a bug to surface.
    ref = _ref("Smith", doi="doi:10.1234/abc")
    issues = check_doi_format(ref)
    assert any(i.code == "doi_malformed" for i in issues)


def test_year_format_accepts_four_digits():
    assert check_year_format(_ref("Smith", year="2020")) == []


def test_year_format_accepts_n_d():
    assert check_year_format(_ref("Smith", year="n.d.")) == []


def test_year_format_rejects_two_digit_year():
    issues = check_year_format(_ref("Smith", year="20"))
    assert any(i.code == "year_malformed" for i in issues)


def test_title_sentence_case_flags_title_case():
    issues = check_title_sentence_case(_ref("Smith", title="A Paper About Things"))
    assert any(i.code == "title_not_sentence_case" for i in issues)


def test_title_sentence_case_accepts_sentence_case():
    assert check_title_sentence_case(_ref("Smith", title="A paper about things")) == []
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/validators/formatting/test_cross_cutting.py -v`
Expected: import errors.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/validators/formatting/__init__.py
```

```python
# packages/engine/src/apa7_validator/validators/formatting/cross_cutting.py
from __future__ import annotations

import re

from apa7_validator.models import Issue, Reference
from apa7_validator.validators.base import IssueBuilder

_REF_BUILDER = IssueBuilder(target_kind="reference")
_GLOBAL_BUILDER = IssueBuilder(target_kind="global")

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_YEAR_RE = re.compile(r"^(?:\d{4}[a-z]?|n\.d\.)$")


def check_alphabetical_order(refs: list[Reference]) -> list[Issue]:
    issues: list[Issue] = []
    last_key = ""
    for ref in refs:
        if not ref.authors:
            continue
        key = ref.authors[0].family.lower()
        if last_key and key < last_key:
            issues.append(
                _GLOBAL_BUILDER.warning(
                    code="references_not_alphabetised",
                    message=f"Reference '{ref.authors[0].family}' is out of order",
                    position=ref.position,
                    suggestion="Sort reference list alphabetically by first author's family name",
                )
            )
        last_key = key
    return issues


def check_doi_format(ref: Reference) -> list[Issue]:
    if ref.doi is None:
        return []
    if not _DOI_RE.match(ref.doi):
        return [
            _REF_BUILDER.error(
                code="doi_malformed",
                message=f"DOI '{ref.doi}' is not in the expected '10.<registrant>/<suffix>' form",
                position=ref.position,
                suggestion="Format DOIs as 'https://doi.org/10.xxxx/yyyy' with the bare DOI starting '10.'",
            )
        ]
    return []


def check_year_format(ref: Reference) -> list[Issue]:
    if not _YEAR_RE.match(ref.year):
        return [
            _REF_BUILDER.error(
                code="year_malformed",
                message=f"Year '{ref.year}' is not four digits or 'n.d.'",
                position=ref.position,
                suggestion="Use a four-digit year, 'n.d.' for no date, or '2020a'-style suffixes for same-year disambiguation",
            )
        ]
    return []


def _is_sentence_case(title: str) -> bool:
    words = title.split()
    if not words:
        return True
    # First word capitalised, others lowercase except after a colon or proper noun.
    for i, word in enumerate(words):
        if i == 0:
            continue
        if word[:1].isupper() and word.lower() not in {"i"}:
            # Allow capitalised word if preceded by ':' or '.', or if it's clearly a proper noun
            # (heuristic: contains a non-leading capital, e.g. "DNA", "iPhone").
            prev = words[i - 1]
            if prev.endswith(":") or prev.endswith("."):
                continue
            if any(c.isupper() for c in word[1:]):
                continue
            return False
    return True


def check_title_sentence_case(ref: Reference) -> list[Issue]:
    if not ref.title:
        return []
    if not _is_sentence_case(ref.title):
        return [
            _REF_BUILDER.warning(
                code="title_not_sentence_case",
                message=f"Title '{ref.title}' appears to use title case",
                position=ref.position,
                suggestion="Use sentence case for article and book titles: capitalise only the first word and proper nouns",
            )
        ]
    return []
```

```python
# packages/engine/tests/validators/formatting/__init__.py
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/validators/formatting/test_cross_cutting.py -v`
Expected: 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/engine/src/apa7_validator/validators/formatting/ packages/engine/tests/validators/formatting/
git commit -m "feat(engine): add cross-cutting formatting rules (alphabetisation, DOI, year, sentence case)"
```

---

### Task 18: Per-type formatting rules — journal article

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/journal.py`
- Create: `packages/engine/tests/validators/formatting/test_journal.py`

Journal-specific rules:
- `R-J-1`: Volume number present (required for APA 7 journal articles).
- `R-J-2`: Issue present unless the journal is unpaginated/continuous.
- `R-J-3`: Page range present (or `e<id>` for article-level identifiers — leave as a follow-up; for v1 we just require *some* page indicator).
- `R-J-4`: DOI present when an article has one (we cannot truly know; warn if `doi` is `None`).

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/formatting/test_journal.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.journal import check_journal


def _journal(**kw) -> Reference:
    defaults = dict(
        raw="x",
        ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020",
        title="A paper",
        container="Journal of Things",
        volume="5",
        issue="2",
        pages="100-120",
        doi="10.1234/jot.2020.05",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_journal_has_no_issues():
    assert check_journal(_journal()) == []


def test_missing_volume_emits_error():
    issues = check_journal(_journal(volume=None))
    assert any(i.code == "journal_missing_volume" for i in issues)


def test_missing_pages_emits_warning():
    issues = check_journal(_journal(pages=None))
    assert any(i.code == "journal_missing_pages" for i in issues)


def test_missing_doi_emits_info():
    issues = check_journal(_journal(doi=None))
    assert any(i.code == "journal_missing_doi" for i in issues)
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/validators/formatting/test_journal.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/validators/formatting/journal.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_journal(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.JOURNAL_ARTICLE:
        return []
    issues: list[Issue] = []
    if not ref.volume:
        issues.append(
            _B.error(
                code="journal_missing_volume",
                message="Journal article is missing a volume number",
                position=ref.position,
                suggestion="Add the volume number after the journal name: 'Journal Name, 5(2), 100-120'",
            )
        )
    if not ref.pages:
        issues.append(
            _B.warning(
                code="journal_missing_pages",
                message="Journal article is missing a page range",
                position=ref.position,
                suggestion="Add a page range or article identifier (e.g., 100-120 or e12345)",
            )
        )
    if not ref.doi:
        issues.append(
            _B.info(
                code="journal_missing_doi",
                message="Journal article is missing a DOI",
                position=ref.position,
                suggestion="Include the DOI as 'https://doi.org/10.xxxx/yyyy' when one is available",
            )
        )
    return issues
```

- [ ] **Step 4: Run tests to confirm pass**

Run: `uv run pytest packages/engine/tests/validators/formatting/test_journal.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/engine/src/apa7_validator/validators/formatting/journal.py packages/engine/tests/validators/formatting/test_journal.py
git commit -m "feat(engine): add journal article formatting rules"
```

---

### Task 19: Per-type formatting rules — book

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/book.py`
- Create: `packages/engine/tests/validators/formatting/test_book.py`

Rules:
- `R-B-1`: Publisher present.
- `R-B-2`: Books published from 2000 should ideally include a DOI when available (info-level only).

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/formatting/test_book.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.book import check_book


def _book(**kw) -> Reference:
    defaults = dict(
        raw="x", ref_type=ReferenceType.BOOK,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020", title="A book", publisher="Earth Press",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_book_has_no_issues():
    assert check_book(_book()) == []


def test_missing_publisher_emits_error():
    issues = check_book(_book(publisher=None))
    assert any(i.code == "book_missing_publisher" for i in issues)
```

- [ ] **Step 2: Run failure**

Run: `uv run pytest packages/engine/tests/validators/formatting/test_book.py -v`
Expected: import error.

- [ ] **Step 3: Implement**

```python
# packages/engine/src/apa7_validator/validators/formatting/book.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_book(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.BOOK:
        return []
    issues: list[Issue] = []
    if not ref.publisher:
        issues.append(
            _B.error(
                code="book_missing_publisher",
                message="Book reference is missing the publisher",
                position=ref.position,
                suggestion="Include the publisher after the title: 'Title. Publisher.'",
            )
        )
    return issues
```

- [ ] **Step 4: Pass + commit**

```bash
uv run pytest packages/engine/tests/validators/formatting/test_book.py -v
git add packages/engine/src/apa7_validator/validators/formatting/book.py packages/engine/tests/validators/formatting/test_book.py
git commit -m "feat(engine): add book formatting rules"
```

---

### Task 20: Per-type formatting rules — book chapter

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/book_chapter.py`
- Create: `packages/engine/tests/validators/formatting/test_book_chapter.py`

Rules:
- `R-BC-1`: Editor (`extras["editors"]`) present.
- `R-BC-2`: Container (book title) present.
- `R-BC-3`: Pages present.
- `R-BC-4`: Publisher present.

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/formatting/test_book_chapter.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.book_chapter import check_book_chapter


def _chapter(**kw) -> Reference:
    defaults = dict(
        raw="x", ref_type=ReferenceType.BOOK_CHAPTER,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020", title="A chapter", container="A Book",
        pages="100-120", publisher="Earth Press",
        extras={"editors": "K. Editor"},
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_chapter_has_no_issues():
    assert check_book_chapter(_chapter()) == []


def test_missing_editor_emits_error():
    issues = check_book_chapter(_chapter(extras={}))
    assert any(i.code == "chapter_missing_editor" for i in issues)


def test_missing_container_emits_error():
    issues = check_book_chapter(_chapter(container=None))
    assert any(i.code == "chapter_missing_book_title" for i in issues)


def test_missing_pages_emits_error():
    issues = check_book_chapter(_chapter(pages=None))
    assert any(i.code == "chapter_missing_pages" for i in issues)


def test_missing_publisher_emits_error():
    issues = check_book_chapter(_chapter(publisher=None))
    assert any(i.code == "chapter_missing_publisher" for i in issues)
```

- [ ] **Step 2: Run failure + implement + pass + commit**

```python
# packages/engine/src/apa7_validator/validators/formatting/book_chapter.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_book_chapter(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.BOOK_CHAPTER:
        return []
    issues: list[Issue] = []
    if not ref.extras.get("editors"):
        issues.append(_B.error(
            code="chapter_missing_editor",
            message="Book chapter is missing editor information ('In X (Ed.), Title')",
            position=ref.position,
            suggestion="Add 'In <Editor Name> (Ed.), <Book Title>' before the page range",
        ))
    if not ref.container:
        issues.append(_B.error(
            code="chapter_missing_book_title",
            message="Book chapter is missing the containing book title",
            position=ref.position,
            suggestion="Include the book title after 'In <Editor> (Ed.),'",
        ))
    if not ref.pages:
        issues.append(_B.error(
            code="chapter_missing_pages",
            message="Book chapter is missing a page range",
            position=ref.position,
            suggestion="Include the chapter's page range: '(pp. 100-120)'",
        ))
    if not ref.publisher:
        issues.append(_B.error(
            code="chapter_missing_publisher",
            message="Book chapter is missing the publisher",
            position=ref.position,
            suggestion="Include the publisher after the page range",
        ))
    return issues
```

Run: `uv run pytest packages/engine/tests/validators/formatting/test_book_chapter.py -v`
Expected: 5 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/formatting/book_chapter.py packages/engine/tests/validators/formatting/test_book_chapter.py
git commit -m "feat(engine): add book chapter formatting rules"
```

---

### Task 21: Per-type formatting rules — website

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/website.py`
- Create: `packages/engine/tests/validators/formatting/test_website.py`

Rules:
- `R-W-1`: URL present (always required for websites).
- `R-W-2`: Container (site name) present unless author = site name.
- `R-W-3`: Retrieved-date guidance: APA 7 requires a retrieval date *only* when the page is expected to change without being archived. We can't tell automatically; emit `info` if `year == "n.d."` and the URL is not on `archive.org` or `web.archive.org`, suggesting a retrieval date.

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/formatting/test_website.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.website import check_website


def _site(**kw) -> Reference:
    defaults = dict(
        raw="x", ref_type=ReferenceType.WEBSITE,
        authors=[Author(family="WHO", given_initials="")],
        year="2022", title="A page",
        container="WHO", url="https://who.int/x",
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_site_has_no_issues():
    assert check_website(_site()) == []


def test_missing_url_emits_error():
    issues = check_website(_site(url=None))
    assert any(i.code == "website_missing_url" for i in issues)


def test_no_date_emits_retrieval_info_when_not_archived():
    issues = check_website(_site(year="n.d.", url="https://example.com/live"))
    assert any(i.code == "website_consider_retrieval_date" for i in issues)


def test_no_date_archived_url_does_not_emit_retrieval_hint():
    issues = check_website(
        _site(year="n.d.", url="https://web.archive.org/web/2023*/example.com")
    )
    assert all(i.code != "website_consider_retrieval_date" for i in issues)
```

- [ ] **Step 2: Implement, pass, commit**

```python
# packages/engine/src/apa7_validator/validators/formatting/website.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")
_ARCHIVED = ("archive.org", "web.archive.org")


def check_website(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.WEBSITE:
        return []
    issues: list[Issue] = []
    if not ref.url:
        issues.append(_B.error(
            code="website_missing_url",
            message="Website reference is missing a URL",
            position=ref.position,
            suggestion="Include the page URL at the end of the reference",
        ))
    if ref.year == "n.d." and ref.url and not any(host in ref.url for host in _ARCHIVED):
        issues.append(_B.info(
            code="website_consider_retrieval_date",
            message="Source with no date that may change over time: consider including a retrieval date",
            position=ref.position,
            suggestion="Format: 'Retrieved <Month Day, Year>, from <URL>' before the URL",
        ))
    return issues
```

Run: `uv run pytest packages/engine/tests/validators/formatting/test_website.py -v`
Expected: 4 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/formatting/website.py packages/engine/tests/validators/formatting/test_website.py
git commit -m "feat(engine): add website formatting rules"
```

---

### Task 22: Per-type formatting rules — report

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/report.py`
- Create: `packages/engine/tests/validators/formatting/test_report.py`

Rules:
- `R-R-1`: Publisher present.
- `R-R-2`: When `extras["report_number"]` is missing but the title hints at a report (`hint`), emit info-level reminder.

- [ ] **Step 1: Tests + implementation + commit**

```python
# packages/engine/tests/validators/formatting/test_report.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.report import check_report


def _report(**kw) -> Reference:
    defaults = dict(
        raw="x", ref_type=ReferenceType.REPORT,
        authors=[Author(family="ABS", given_initials="")],
        year="2023", title="Population trends",
        publisher="ABS",
        extras={"report_number": "3101.0"},
        position=Position(0, 1),
    )
    defaults.update(kw)
    return Reference(**defaults)


def test_complete_report_has_no_issues():
    assert check_report(_report()) == []


def test_missing_publisher_emits_error():
    issues = check_report(_report(publisher=None))
    assert any(i.code == "report_missing_publisher" for i in issues)
```

```python
# packages/engine/src/apa7_validator/validators/formatting/report.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_report(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.REPORT:
        return []
    issues: list[Issue] = []
    if not ref.publisher:
        issues.append(_B.error(
            code="report_missing_publisher",
            message="Report reference is missing the publisher / issuing organisation",
            position=ref.position,
            suggestion="Include the issuing body after the title (or after the report number)",
        ))
    return issues
```

Run: `uv run pytest packages/engine/tests/validators/formatting/test_report.py -v`
Expected: 2 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/formatting/report.py packages/engine/tests/validators/formatting/test_report.py
git commit -m "feat(engine): add report formatting rules"
```

---

### Task 23: Per-type formatting rules — AI source

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/formatting/ai_source.py`
- Create: `packages/engine/tests/validators/formatting/test_ai_source.py`

Rules:
- `R-AI-1`: `extras["model_kind"]` present (the `[Large language model]` bracket).
- `R-AI-2`: URL present.
- `R-AI-3`: APA 7 currently recommends treating the developer (e.g., OpenAI) as author. Warn if `authors[0].family` looks like a personal name (has comma-formatted initials) rather than an organisation.

- [ ] **Step 1: Tests + implementation + commit**

```python
# packages/engine/tests/validators/formatting/test_ai_source.py
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.formatting.ai_source import check_ai_source


def _ai(**kw) -> Reference:
    defaults = dict(
        raw="x", ref_type=ReferenceType.AI_SOURCE,
        authors=[Author(family="OpenAI", given_initials="")],
        year="2023", title="ChatGPT (Mar 14 version)",
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
```

```python
# packages/engine/src/apa7_validator/validators/formatting/ai_source.py
from __future__ import annotations

from apa7_validator.models import Issue, Reference, ReferenceType
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


def check_ai_source(ref: Reference) -> list[Issue]:
    if ref.ref_type is not ReferenceType.AI_SOURCE:
        return []
    issues: list[Issue] = []
    if not ref.extras.get("model_kind"):
        issues.append(_B.error(
            code="ai_missing_model_kind",
            message="AI-generated source is missing the bracketed model descriptor",
            position=ref.position,
            suggestion="Add a description in brackets, e.g. '[Large language model]'",
        ))
    if not ref.url:
        issues.append(_B.error(
            code="ai_missing_url",
            message="AI-generated source is missing the model's URL",
            position=ref.position,
            suggestion="Include the URL where the model is accessed (e.g., https://chat.openai.com)",
        ))
    if ref.authors and ref.authors[0].given_initials:
        issues.append(_B.warning(
            code="ai_author_should_be_developer",
            message=(
                "AI-source author looks like a personal name; APA 7 currently treats the "
                "developer (e.g., OpenAI) as author"
            ),
            position=ref.position,
            suggestion="Use the developing organisation as the author",
        ))
    return issues
```

Run: `uv run pytest packages/engine/tests/validators/formatting/test_ai_source.py -v`
Expected: 4 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/formatting/ai_source.py packages/engine/tests/validators/formatting/test_ai_source.py
git commit -m "feat(engine): add AI-source formatting rules"
```

---

### Task 24: Cross-matching validator

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/cross_matching.py`
- Create: `packages/engine/tests/validators/test_cross_matching.py`

Behaviour:
- For each `Citation`, find a matching `Reference` by `(first_author_family.lower(), year)`. Treat `"et al."` and ampersand surface forms as matching their first surname.
- Citations without matches → `error: citation_without_reference`.
- References without any citation → `warning: reference_uncited`.
- Same (family, year) appearing on multiple references → `warning: ambiguous_match` on each citation that hits more than one.

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/test_cross_matching.py
from apa7_validator.models import Author, Citation, Position, Reference, ReferenceType
from apa7_validator.validators.cross_matching import check_cross_matching


def _ref(family: str, year: str) -> Reference:
    return Reference(
        raw="x", ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year=year, title="A paper", position=Position(0, 1),
    )


def _cit(family: str, year: str, narrative: bool = False) -> Citation:
    return Citation(
        raw="x", authors=[family], year=year, narrative=narrative,
        position=Position(0, 1),
    )


def test_clean_pair_has_no_issues():
    refs = [_ref("Smith", "2020")]
    cits = [_cit("Smith", "2020")]
    assert check_cross_matching(cits, refs) == []


def test_citation_without_reference_emits_error():
    issues = check_cross_matching([_cit("Smith", "2020")], [])
    assert any(i.code == "citation_without_reference" for i in issues)


def test_reference_uncited_emits_warning():
    issues = check_cross_matching([], [_ref("Smith", "2020")])
    assert any(i.code == "reference_uncited" for i in issues)


def test_et_al_matches_first_author():
    refs = [_ref("Smith", "2020")]
    cits = [Citation(
        raw="(Smith et al., 2020)", authors=["Smith et al."], year="2020",
        narrative=False, position=Position(0, 1),
    )]
    assert check_cross_matching(cits, refs) == []


def test_ambiguous_match_emits_warning():
    refs = [_ref("Smith", "2020"), _ref("Smith", "2020")]
    cits = [_cit("Smith", "2020")]
    issues = check_cross_matching(cits, refs)
    assert any(i.code == "ambiguous_match" for i in issues)
```

- [ ] **Step 2: Implement + pass + commit**

```python
# packages/engine/src/apa7_validator/validators/cross_matching.py
from __future__ import annotations

from collections import defaultdict

from apa7_validator.models import Citation, Issue, Reference
from apa7_validator.validators.base import IssueBuilder

_REF_B = IssueBuilder(target_kind="reference")
_CIT_B = IssueBuilder(target_kind="citation")


def _ref_key(ref: Reference) -> tuple[str, str]:
    family = ref.authors[0].family.lower() if ref.authors else ""
    return (family, ref.year)


def _cit_key(cit: Citation) -> tuple[str, str]:
    raw_first = cit.authors[0] if cit.authors else ""
    # Strip "et al." and trailing punctuation.
    family = raw_first.replace("et al.", "").strip().rstrip(",")
    return (family.lower(), cit.year)


def check_cross_matching(cits: list[Citation], refs: list[Reference]) -> list[Issue]:
    issues: list[Issue] = []
    refs_by_key: dict[tuple[str, str], list[Reference]] = defaultdict(list)
    for ref in refs:
        refs_by_key[_ref_key(ref)].append(ref)

    matched_refs: set[int] = set()

    for cit in cits:
        key = _cit_key(cit)
        candidates = refs_by_key.get(key, [])
        if not candidates:
            issues.append(_CIT_B.error(
                code="citation_without_reference",
                message=f"In-text citation '{cit.raw}' has no matching reference list entry",
                position=cit.position,
                suggestion="Add a reference list entry, or correct the author/year in the citation",
            ))
        elif len(candidates) > 1:
            issues.append(_CIT_B.warning(
                code="ambiguous_match",
                message=(
                    f"Citation '{cit.raw}' matches multiple reference list entries; "
                    f"disambiguate by adding letter suffixes (e.g., 2020a, 2020b)"
                ),
                position=cit.position,
                suggestion="Append 'a', 'b', ... to the year of same-author-same-year references",
            ))
            for ref in candidates:
                matched_refs.add(id(ref))
        else:
            matched_refs.add(id(candidates[0]))

    for ref in refs:
        if id(ref) not in matched_refs:
            issues.append(_REF_B.warning(
                code="reference_uncited",
                message=(
                    f"Reference '{ref.authors[0].family if ref.authors else '?'}, {ref.year}' "
                    "is not cited in the body"
                ),
                position=ref.position,
                suggestion="Cite the reference in the body, or remove it from the reference list",
            ))

    return issues
```

Run: `uv run pytest packages/engine/tests/validators/test_cross_matching.py -v`
Expected: 5 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/cross_matching.py packages/engine/tests/validators/test_cross_matching.py
git commit -m "feat(engine): add cross-matching validator (citations <-> references)"
```

---

### Task 25: HTTP client base + Clients dataclass + dry-run

**Files:**
- Create: `packages/engine/src/apa7_validator/clients/__init__.py`
- Create: `packages/engine/src/apa7_validator/clients/base.py`
- Create: `packages/engine/tests/clients/__init__.py`
- Create: `packages/engine/tests/clients/test_base.py`

Design notes:
- Every client function is async and accepts only public identifiers (DOI string, ISBN string, URL string). No `text`, `essay`, `body`, or `content` parameters — a structural test in Task 40 enforces this.
- `Clients` is the injectable bundle the engine takes. `Clients.dry_run()` returns a bundle that never makes network calls — every lookup returns `LookupResult.unavailable()`.

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/clients/test_base.py
import asyncio

import pytest

from apa7_validator.clients.base import Clients, LookupResult


def test_lookup_result_found_carries_metadata():
    r = LookupResult.found({"title": "x"})
    assert r.status == "found"
    assert r.metadata == {"title": "x"}


def test_lookup_result_not_found():
    assert LookupResult.not_found().status == "not_found"


def test_lookup_result_unavailable():
    assert LookupResult.unavailable("offline").status == "unavailable"


def test_dry_run_clients_returns_unavailable_for_all():
    clients = Clients.dry_run()

    async def go() -> None:
        assert (await clients.crossref.lookup_doi("10.1234/abc")).status == "unavailable"
        assert (await clients.unpaywall.lookup_doi("10.1234/abc")).status == "unavailable"
        assert (await clients.openlibrary.lookup_isbn("9780000000000")).status == "unavailable"
        assert (await clients.url_check.check("https://example.com")).status == "unavailable"

    asyncio.run(go())


def test_clients_construction_rejects_text_like_args():
    with pytest.raises(TypeError):
        # The whole point of dry_run: don't accept content-bearing params anywhere.
        Clients.dry_run().crossref.lookup_doi("10.1234/abc", text="hi")  # type: ignore[call-arg]
```

- [ ] **Step 2: Implement + pass**

```python
# packages/engine/src/apa7_validator/clients/base.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

LookupStatus = Literal["found", "not_found", "unavailable"]


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    metadata: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    @classmethod
    def found(cls, metadata: dict[str, Any]) -> LookupResult:
        return cls(status="found", metadata=metadata)

    @classmethod
    def not_found(cls) -> LookupResult:
        return cls(status="not_found")

    @classmethod
    def unavailable(cls, reason: str = "") -> LookupResult:
        return cls(status="unavailable", reason=reason)


class CrossRefClient(Protocol):
    async def lookup_doi(self, doi: str) -> LookupResult: ...


class UnpaywallClient(Protocol):
    async def lookup_doi(self, doi: str) -> LookupResult: ...


class OpenLibraryClient(Protocol):
    async def lookup_isbn(self, isbn: str) -> LookupResult: ...


class UrlCheckClient(Protocol):
    async def check(self, url: str) -> LookupResult: ...


class _DryClient:
    async def lookup_doi(self, doi: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")

    async def check(self, url: str) -> LookupResult:
        return LookupResult.unavailable("dry-run")


@dataclass(frozen=True, slots=True)
class Clients:
    crossref: CrossRefClient
    unpaywall: UnpaywallClient
    openlibrary: OpenLibraryClient
    url_check: UrlCheckClient

    @classmethod
    def dry_run(cls) -> Clients:
        dry = _DryClient()
        return cls(crossref=dry, unpaywall=dry, openlibrary=dry, url_check=dry)
```

```python
# packages/engine/src/apa7_validator/clients/__init__.py
from .base import (
    Clients,
    CrossRefClient,
    LookupResult,
    LookupStatus,
    OpenLibraryClient,
    UnpaywallClient,
    UrlCheckClient,
)

__all__ = [
    "Clients",
    "CrossRefClient",
    "LookupResult",
    "LookupStatus",
    "OpenLibraryClient",
    "UnpaywallClient",
    "UrlCheckClient",
]
```

```python
# packages/engine/tests/clients/__init__.py
```

Run: `uv run pytest packages/engine/tests/clients/test_base.py -v`
Expected: 5 tests pass.

- [ ] **Step 3: Commit**

```bash
git add packages/engine/src/apa7_validator/clients/ packages/engine/tests/clients/
git commit -m "feat(engine): add Clients dataclass and LookupResult with dry-run mode"
```

---

### Task 26: CrossRef client

**Files:**
- Create: `packages/engine/src/apa7_validator/clients/crossref.py`
- Modify: `packages/engine/src/apa7_validator/clients/__init__.py`
- Create: `packages/engine/tests/clients/test_crossref.py`
- Create: `packages/engine/tests/fixtures/cassettes/.gitkeep`

- [ ] **Step 1: Write failing tests with VCR cassette stub**

```python
# packages/engine/tests/clients/test_crossref.py
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]

from apa7_validator.clients.crossref import HttpxCrossRefClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="none",  # CI: replay only. Use "new_episodes" locally to record.
    filter_headers=["authorization", "user-agent"],
)


@pytest.mark.asyncio
@my_vcr.use_cassette("crossref_found.yaml")
async def test_lookup_known_doi_returns_found():
    client = HttpxCrossRefClient(user_agent="apa7-validator-test/0.1 (test@example.com)")
    result = await client.lookup_doi("10.1037/0003-066X.59.1.29")
    assert result.status == "found"
    assert "title" in result.metadata


@pytest.mark.asyncio
@my_vcr.use_cassette("crossref_not_found.yaml")
async def test_lookup_unknown_doi_returns_not_found():
    client = HttpxCrossRefClient(user_agent="apa7-validator-test/0.1 (test@example.com)")
    result = await client.lookup_doi("10.9999/this-doi-does-not-exist")
    assert result.status == "not_found"
```

- [ ] **Step 2: Implement the CrossRef client**

```python
# packages/engine/src/apa7_validator/clients/crossref.py
from __future__ import annotations

import httpx

from .base import LookupResult


class HttpxCrossRefClient:
    """Look up DOIs against api.crossref.org.

    Only DOIs are sent over the wire. The user-agent string is required by CrossRef's
    polite-pool guidelines and includes a contact email passed by the caller.
    """

    BASE = "https://api.crossref.org/works/"

    def __init__(self, user_agent: str, timeout_s: float = 10.0) -> None:
        self._headers = {"User-Agent": user_agent}
        self._timeout_s = timeout_s

    async def lookup_doi(self, doi: str) -> LookupResult:
        url = self.BASE + doi
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout_s) as c:
                resp = await c.get(url)
        except httpx.HTTPError as exc:
            return LookupResult.unavailable(f"http_error: {type(exc).__name__}")
        if resp.status_code == 404:
            return LookupResult.not_found()
        if resp.status_code >= 500 or resp.status_code == 429:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        if resp.status_code != 200:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        data = resp.json().get("message", {})
        return LookupResult.found({
            "title": (data.get("title") or [""])[0],
            "type": data.get("type", ""),
            "issued": (data.get("issued") or {}).get("date-parts", [[None]])[0][0],
        })
```

Update `packages/engine/src/apa7_validator/clients/__init__.py` to also export `HttpxCrossRefClient`.

- [ ] **Step 3: Record the cassettes (one-time, local)**

Run locally (CI runs with `record_mode="none"`):

```bash
RECORD_MODE=new_episodes uv run pytest packages/engine/tests/clients/test_crossref.py -v
```

If the cassettes don't exist yet, this requires a one-line tweak to `test_crossref.py` to honour an env var:

```python
import os
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
    filter_headers=["authorization", "user-agent"],
)
```

Add this and re-run with `RECORD_MODE=new_episodes` once to populate `crossref_found.yaml` and `crossref_not_found.yaml`, then commit them.

- [ ] **Step 4: Run replay tests**

Run: `uv run pytest packages/engine/tests/clients/test_crossref.py -v`
Expected: 2 tests pass against cassettes.

- [ ] **Step 5: Commit**

```bash
git add packages/engine/src/apa7_validator/clients/ packages/engine/tests/clients/test_crossref.py packages/engine/tests/fixtures/cassettes/
git commit -m "feat(engine): add CrossRef DOI lookup client with VCR cassette tests"
```

---

### Task 27: Unpaywall client

**Files:**
- Create: `packages/engine/src/apa7_validator/clients/unpaywall.py`
- Modify: `packages/engine/src/apa7_validator/clients/__init__.py`
- Create: `packages/engine/tests/clients/test_unpaywall.py`

- [ ] **Step 1: Write failing tests using cassettes**

```python
# packages/engine/tests/clients/test_unpaywall.py
import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]

from apa7_validator.clients.unpaywall import HttpxUnpaywallClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
    filter_query_parameters=["email"],
)


@pytest.mark.asyncio
@my_vcr.use_cassette("unpaywall_found_oa.yaml")
async def test_known_oa_doi_returns_found_with_oa_metadata():
    client = HttpxUnpaywallClient(contact_email="test@example.com")
    result = await client.lookup_doi("10.7717/peerj.4375")
    assert result.status == "found"
    assert "is_oa" in result.metadata


@pytest.mark.asyncio
@my_vcr.use_cassette("unpaywall_not_found.yaml")
async def test_unknown_doi_returns_not_found():
    client = HttpxUnpaywallClient(contact_email="test@example.com")
    result = await client.lookup_doi("10.9999/no-such-doi")
    assert result.status == "not_found"
```

- [ ] **Step 2: Implement + record cassettes + commit**

```python
# packages/engine/src/apa7_validator/clients/unpaywall.py
from __future__ import annotations

import httpx

from .base import LookupResult


class HttpxUnpaywallClient:
    """Look up DOIs against api.unpaywall.org.

    Sends only the DOI plus the configured contact email (Unpaywall's API
    requirement; not user PII).
    """

    BASE = "https://api.unpaywall.org/v2/"

    def __init__(self, contact_email: str, timeout_s: float = 10.0) -> None:
        if not contact_email:
            raise ValueError("Unpaywall requires a contact email")
        self._email = contact_email
        self._timeout_s = timeout_s

    async def lookup_doi(self, doi: str) -> LookupResult:
        url = f"{self.BASE}{doi}?email={self._email}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as c:
                resp = await c.get(url)
        except httpx.HTTPError as exc:
            return LookupResult.unavailable(f"http_error: {type(exc).__name__}")
        if resp.status_code == 404:
            return LookupResult.not_found()
        if resp.status_code >= 500 or resp.status_code == 429:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        if resp.status_code != 200:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        data = resp.json()
        return LookupResult.found({
            "is_oa": bool(data.get("is_oa")),
            "oa_locations_count": len(data.get("oa_locations", [])),
        })
```

Record cassettes locally with `RECORD_MODE=new_episodes`, commit them, and confirm replay passes.

```bash
git add packages/engine/src/apa7_validator/clients/ packages/engine/tests/clients/test_unpaywall.py packages/engine/tests/fixtures/cassettes/unpaywall_*.yaml
git commit -m "feat(engine): add Unpaywall client with VCR cassette tests"
```

---

### Task 28: OpenLibrary client

**Files:**
- Create: `packages/engine/src/apa7_validator/clients/openlibrary.py`
- Modify: `packages/engine/src/apa7_validator/clients/__init__.py`
- Create: `packages/engine/tests/clients/test_openlibrary.py`

- [ ] **Step 1: Tests + implementation + cassettes + commit**

```python
# packages/engine/tests/clients/test_openlibrary.py
import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]

from apa7_validator.clients.openlibrary import HttpxOpenLibraryClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
)


@pytest.mark.asyncio
@my_vcr.use_cassette("openlibrary_found.yaml")
async def test_known_isbn_returns_found():
    client = HttpxOpenLibraryClient()
    result = await client.lookup_isbn("9780201896831")
    assert result.status == "found"


@pytest.mark.asyncio
@my_vcr.use_cassette("openlibrary_not_found.yaml")
async def test_unknown_isbn_returns_not_found():
    client = HttpxOpenLibraryClient()
    result = await client.lookup_isbn("9999999999999")
    assert result.status == "not_found"
```

```python
# packages/engine/src/apa7_validator/clients/openlibrary.py
from __future__ import annotations

import httpx

from .base import LookupResult


class HttpxOpenLibraryClient:
    BASE = "https://openlibrary.org/isbn/"

    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        url = f"{self.BASE}{isbn}.json"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s, follow_redirects=True) as c:
                resp = await c.get(url)
        except httpx.HTTPError as exc:
            return LookupResult.unavailable(f"http_error: {type(exc).__name__}")
        if resp.status_code == 404:
            return LookupResult.not_found()
        if resp.status_code >= 500 or resp.status_code == 429:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        if resp.status_code != 200:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        data = resp.json()
        return LookupResult.found({"title": data.get("title", "")})
```

Record cassettes, commit:

```bash
git add packages/engine/src/apa7_validator/clients/openlibrary.py packages/engine/tests/clients/test_openlibrary.py packages/engine/tests/fixtures/cassettes/openlibrary_*.yaml packages/engine/src/apa7_validator/clients/__init__.py
git commit -m "feat(engine): add OpenLibrary ISBN client with VCR cassette tests"
```

---

### Task 29: URL liveness check

**Files:**
- Create: `packages/engine/src/apa7_validator/clients/url_check.py`
- Modify: `packages/engine/src/apa7_validator/clients/__init__.py`
- Create: `packages/engine/tests/clients/test_url_check.py`

- [ ] **Step 1: Tests + implementation + commit**

```python
# packages/engine/tests/clients/test_url_check.py
import os
from pathlib import Path

import pytest
import vcr  # type: ignore[import-untyped]

from apa7_validator.clients.url_check import HttpxUrlCheckClient

CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode=os.environ.get("RECORD_MODE", "none"),
)


@pytest.mark.asyncio
@my_vcr.use_cassette("url_check_alive.yaml")
async def test_live_url_returns_found():
    client = HttpxUrlCheckClient()
    result = await client.check("https://example.com")
    assert result.status == "found"


@pytest.mark.asyncio
@my_vcr.use_cassette("url_check_404.yaml")
async def test_404_url_returns_not_found():
    client = HttpxUrlCheckClient()
    result = await client.check("https://example.com/definitely-not-here-xyz")
    assert result.status == "not_found"
```

```python
# packages/engine/src/apa7_validator/clients/url_check.py
from __future__ import annotations

import httpx

from .base import LookupResult


class HttpxUrlCheckClient:
    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s

    async def check(self, url: str) -> LookupResult:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_s,
                follow_redirects=True,
            ) as c:
                resp = await c.head(url)
                if resp.status_code == 405:
                    # Some servers reject HEAD; retry with GET.
                    resp = await c.get(url)
        except httpx.HTTPError as exc:
            return LookupResult.unavailable(f"http_error: {type(exc).__name__}")
        if resp.status_code == 404 or resp.status_code == 410:
            return LookupResult.not_found()
        if resp.status_code >= 500:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        if resp.status_code >= 400:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        return LookupResult.found({"final_url": str(resp.url)})
```

Record cassettes, commit:

```bash
git add packages/engine/src/apa7_validator/clients/url_check.py packages/engine/tests/clients/test_url_check.py packages/engine/tests/fixtures/cassettes/url_check_*.yaml packages/engine/src/apa7_validator/clients/__init__.py
git commit -m "feat(engine): add URL liveness check client with VCR cassette tests"
```

---

### Task 30: Existence validator

**Files:**
- Create: `packages/engine/src/apa7_validator/validators/existence.py`
- Create: `packages/engine/tests/validators/test_existence.py`

Behaviour:
- For each `Reference`, pick the appropriate identifier and client:
  - Has `doi` → `crossref.lookup_doi` (and optionally `unpaywall` as supplementary info).
  - Has `isbn` → `openlibrary.lookup_isbn`.
  - Has `url` only → `url_check.check`.
  - None of the above → no check (info only).
- `found` → no issue.
- `not_found` → `error: doi_not_found` / `isbn_not_found` / `url_not_found`.
- `unavailable` → per-reference info note `existence_check_unavailable`; record `existence` in `degraded_checks` when ANY lookup is unavailable.
- Runs lookups concurrently with `asyncio.gather`.

- [ ] **Step 1: Write failing tests**

```python
# packages/engine/tests/validators/test_existence.py
import asyncio
from dataclasses import dataclass

import pytest

from apa7_validator.clients.base import Clients, LookupResult
from apa7_validator.models import Author, Position, Reference, ReferenceType
from apa7_validator.validators.existence import check_existence


@dataclass
class _StubClient:
    impl: callable  # type: ignore[type-arg]

    async def lookup_doi(self, doi: str) -> LookupResult:
        return self.impl(doi)

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        return self.impl(isbn)

    async def check(self, url: str) -> LookupResult:
        return self.impl(url)


def _clients(impl):
    c = _StubClient(impl=impl)
    return Clients(crossref=c, unpaywall=c, openlibrary=c, url_check=c)


def _ref_with_doi(doi: str) -> Reference:
    return Reference(
        raw="x", ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family="Smith", given_initials="J.")],
        year="2020", title="x", doi=doi, position=Position(0, 1),
    )


@pytest.mark.asyncio
async def test_found_doi_emits_no_issue():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, degraded = await check_existence(refs, _clients(lambda _id: LookupResult.found({})))
    assert issues == []
    assert degraded == []


@pytest.mark.asyncio
async def test_not_found_doi_emits_error():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, _ = await check_existence(refs, _clients(lambda _id: LookupResult.not_found()))
    assert any(i.code == "doi_not_found" for i in issues)


@pytest.mark.asyncio
async def test_unavailable_doi_emits_info_and_records_degradation():
    refs = [_ref_with_doi("10.1234/abc")]
    issues, degraded = await check_existence(
        refs, _clients(lambda _id: LookupResult.unavailable("offline"))
    )
    assert any(i.code == "existence_check_unavailable" for i in issues)
    assert "existence" in degraded
```

- [ ] **Step 2: Implement + pass + commit**

```python
# packages/engine/src/apa7_validator/validators/existence.py
from __future__ import annotations

import asyncio

from apa7_validator.clients.base import Clients, LookupResult
from apa7_validator.models import Issue, Reference
from apa7_validator.validators.base import IssueBuilder

_B = IssueBuilder(target_kind="reference")


async def _check_one(ref: Reference, clients: Clients) -> list[Issue]:
    if ref.doi:
        result = await clients.crossref.lookup_doi(ref.doi)
        return _issues_from(result, ref, kind="doi")
    if ref.isbn:
        result = await clients.openlibrary.lookup_isbn(ref.isbn)
        return _issues_from(result, ref, kind="isbn")
    if ref.url:
        result = await clients.url_check.check(ref.url)
        return _issues_from(result, ref, kind="url")
    return []


def _issues_from(result: LookupResult, ref: Reference, *, kind: str) -> list[Issue]:
    if result.status == "found":
        return []
    if result.status == "not_found":
        return [_B.error(
            code=f"{kind}_not_found",
            message=f"{kind.upper()} not found in lookup service",
            position=ref.position,
            suggestion=f"Verify the {kind.upper()} value (typos are common)",
        )]
    return [_B.info(
        code="existence_check_unavailable",
        message=f"Could not verify {kind.upper()} existence ({result.reason or 'unknown'})",
        position=ref.position,
        suggestion="Re-run the check when the lookup service is available",
    )]


async def check_existence(
    refs: list[Reference], clients: Clients,
) -> tuple[list[Issue], list[str]]:
    """Returns (issues, degraded_checks). `existence` appears in degraded_checks
    if any reference's lookup returned `unavailable`."""
    results = await asyncio.gather(*[_check_one(ref, clients) for ref in refs])
    issues = [iss for sub in results for iss in sub]
    degraded = ["existence"] if any(i.code == "existence_check_unavailable" for i in issues) else []
    return issues, degraded
```

Run: `uv run pytest packages/engine/tests/validators/test_existence.py -v`
Expected: 3 tests pass.

```bash
git add packages/engine/src/apa7_validator/validators/existence.py packages/engine/tests/validators/test_existence.py
git commit -m "feat(engine): add existence validator with network-aware degradation"
```

---

### Task 31: Safe logging setup

**Files:**
- Create: `packages/engine/src/apa7_validator/logging.py`
- Create: `packages/engine/tests/test_logging.py`

Behaviour:
- A `safe_log()` helper accepts only fields on an allowlist.
- Disallowed field names raise `ValueError`. This is the structural guarantee referenced in the spec §9.4.

- [ ] **Step 1: Failing tests**

```python
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
        "job_id", "status", "duration_ms", "error_code",
        "reference_count", "issue_count", "degraded_checks",
    }
    assert expected <= SAFE_FIELDS
```

- [ ] **Step 2: Implement + pass + commit**

```python
# packages/engine/src/apa7_validator/logging.py
from __future__ import annotations

import json
import sys
from typing import Any

SAFE_FIELDS: frozenset[str] = frozenset({
    "job_id", "status", "duration_ms", "error_code",
    "reference_count", "issue_count", "degraded_checks",
    "ref_type", "severity", "rule_code",
})


def safe_log(message: str, **fields: Any) -> None:
    bad = set(fields) - SAFE_FIELDS
    if bad:
        raise ValueError(
            f"safe_log refuses field(s) not on the allowlist: {sorted(bad)}. "
            "If you must log a new field, add it to SAFE_FIELDS after privacy review."
        )
    payload = {"msg": message, **fields}
    print(json.dumps(payload), file=sys.stdout)
```

Run: `uv run pytest packages/engine/tests/test_logging.py -v`
Expected: 3 tests pass.

```bash
git add packages/engine/src/apa7_validator/logging.py packages/engine/tests/test_logging.py
git commit -m "feat(engine): add safe_log with allowlisted fields (privacy guarantee)"
```

---

### Task 32: Reporter

**Files:**
- Create: `packages/engine/src/apa7_validator/reporter.py`
- Create: `packages/engine/tests/test_reporter.py`

- [ ] **Step 1: Failing tests**

```python
# packages/engine/tests/test_reporter.py
from apa7_validator.models import Author, Citation, Position, Reference, ReferenceType, Severity
from apa7_validator.reporter import assemble


def _ref(family: str = "Smith") -> Reference:
    return Reference(
        raw="x", ref_type=ReferenceType.JOURNAL_ARTICLE,
        authors=[Author(family=family, given_initials="J.")],
        year="2020", title="x", position=Position(0, 1),
    )


def _cit() -> Citation:
    return Citation(raw="x", authors=["Smith"], year="2020", narrative=False, position=Position(0, 1))


def test_assemble_packs_inputs_into_report():
    rep = assemble(
        references=[_ref()],
        citations=[_cit()],
        formatting_issues=[],
        cross_matching_issues=[],
        existence_issues=[],
        warnings=["no_reference_list_found"],
        degraded_checks=[],
    )
    assert rep.references[0].authors[0].family == "Smith"
    assert rep.warnings == ["no_reference_list_found"]


def test_issues_sorted_by_severity_then_position():
    from apa7_validator.models import Issue
    issues = [
        Issue(code="b", severity=Severity.WARNING, message="m", position=Position(0, 1)),
        Issue(code="a", severity=Severity.ERROR, message="m", position=Position(0, 1)),
    ]
    rep = assemble(
        references=[], citations=[], formatting_issues=issues,
        cross_matching_issues=[], existence_issues=[],
        warnings=[], degraded_checks=[],
    )
    assert rep.issues[0].severity is Severity.ERROR
```

- [ ] **Step 2: Implement + pass + commit**

```python
# packages/engine/src/apa7_validator/reporter.py
from __future__ import annotations

from .models import Citation, Issue, Reference, Report, Severity

_SEVERITY_ORDER = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}


def assemble(
    *,
    references: list[Reference],
    citations: list[Citation],
    formatting_issues: list[Issue],
    cross_matching_issues: list[Issue],
    existence_issues: list[Issue],
    warnings: list[str],
    degraded_checks: list[str],
) -> Report:
    issues = formatting_issues + cross_matching_issues + existence_issues
    issues.sort(key=lambda i: (_SEVERITY_ORDER[i.severity], i.position.start))
    return Report(
        references=references,
        citations=citations,
        issues=issues,
        warnings=warnings,
        degraded_checks=degraded_checks,
    )
```

Run: `uv run pytest packages/engine/tests/test_reporter.py -v`
Expected: 2 tests pass.

```bash
git add packages/engine/src/apa7_validator/reporter.py packages/engine/tests/test_reporter.py
git commit -m "feat(engine): add reporter that assembles the final Report"
```

---

**End of Phase B.** Engine now has all the pieces to take an `ExtractionResult`, parse it, validate it, and produce a `Report`. Phase C wires this into `validate()`, adds annotators (web + DOCX), the privacy structural guarantees, and the CLI.

Suggested checkpoint:

```bash
uv run pytest packages/engine/tests -v
uv run ruff check .
uv run pyright packages/engine/src
```

---

# Phase C — Output + CLI (Tasks 33–45)

End state: `apa7_validator.validate()` and `apa7_validator.annotate_docx()` work end-to-end. The `apa7-check` CLI provides human-readable output, `--json`, and `--annotate <out.docx>`. Structural privacy tests guard against accidental leakage. Engine end-to-end smoke test passes on a curated fixture.

---

### Task 33: Web annotator

**Files:**
- Create: `packages/engine/src/apa7_validator/annotators/__init__.py`
- Create: `packages/engine/src/apa7_validator/annotators/web.py`
- Create: `packages/engine/tests/annotators/__init__.py`
- Create: `packages/engine/tests/annotators/test_web.py`

Behaviour: produce a JSON-serialisable structure the future SPA can consume.

- [ ] **Step 1: Failing tests**

```python
# packages/engine/tests/annotators/test_web.py
from apa7_validator.annotators.web import build_web_annotation
from apa7_validator.models import Issue, Position, Report, Severity


def test_web_annotation_shape():
    rep = Report(
        references=[], citations=[],
        issues=[Issue(code="x", severity=Severity.ERROR, message="m", position=Position(5, 10))],
        warnings=["no_reference_list_found"], degraded_checks=["existence"],
    )
    out = build_web_annotation(rep, source_text="0123456789ABC")
    assert out["warnings"] == ["no_reference_list_found"]
    assert out["degraded_checks"] == ["existence"]
    assert out["annotations"][0]["span"] == [5, 10]
    assert out["annotations"][0]["span_text"] == "56789"
    assert out["annotations"][0]["severity"] == "error"
```

- [ ] **Step 2: Implement + pass + commit**

```python
# packages/engine/src/apa7_validator/annotators/__init__.py
from .web import build_web_annotation

__all__ = ["build_web_annotation"]
```

```python
# packages/engine/src/apa7_validator/annotators/web.py
from __future__ import annotations

from typing import Any

from apa7_validator.models import Report


def build_web_annotation(report: Report, source_text: str) -> dict[str, Any]:
    annotations: list[dict[str, Any]] = []
    for iss in report.issues:
        start, end = iss.position.start, iss.position.end
        annotations.append({
            "code": iss.code,
            "severity": iss.severity.value,
            "message": iss.message,
            "suggestion": iss.suggestion,
            "target_kind": iss.target_kind,
            "span": [start, end],
            "span_text": source_text[start:end],
        })
    return {
        "annotations": annotations,
        "warnings": report.warnings,
        "degraded_checks": report.degraded_checks,
        "reference_count": len(report.references),
        "citation_count": len(report.citations),
    }
```

```python
# packages/engine/tests/annotators/__init__.py
```

Run: `uv run pytest packages/engine/tests/annotators/test_web.py -v`
Expected: 1 test passes.

```bash
git add packages/engine/src/apa7_validator/annotators/ packages/engine/tests/annotators/
git commit -m "feat(engine): add web annotator (JSON for SPA rendering)"
```

---

### Task 34: DOCX annotator — library-choice spike + structure

**Files:**
- Create: `packages/engine/src/apa7_validator/annotators/docx.py`
- Create: `packages/engine/tests/annotators/test_docx_spike.py`
- Create: `docs/superpowers/notes/2026-06-05-docx-comment-injection-spike.md`

This task is **a spike**: confirm that direct OOXML manipulation via `lxml` can inject Word-native comments into a `.docx` produced by `python-docx`. The output of this spike is a 1-page note and a working `inject_comment_xml()` helper. The full annotator (with position-map awareness) lands in Tasks 35–36.

- [ ] **Step 1: Write the spike test**

```python
# packages/engine/tests/annotators/test_docx_spike.py
import io
import zipfile

import docx as pythondocx

from apa7_validator.annotators.docx import inject_comment_xml


def _make_minimal_docx() -> bytes:
    doc = pythondocx.Document()
    doc.add_paragraph("Climate change is well documented (Smith, 2020).")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_inject_comment_xml_adds_comments_part():
    src = _make_minimal_docx()
    out = inject_comment_xml(
        src,
        comments=[{
            "id": "0",
            "author": "apa7",
            "initials": "apa7",
            "date": "2026-06-05T00:00:00Z",
            "text": "Verify DOI.",
            "anchor_paragraph_idx": 0,
            "anchor_text": "Smith, 2020",
        }],
    )
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        names = set(z.namelist())
        assert "word/comments.xml" in names
        # Confirm document.xml carries comment range markers.
        doc_xml = z.read("word/document.xml").decode()
        assert "commentRangeStart" in doc_xml
        assert "commentReference" in doc_xml
```

- [ ] **Step 2: Run to confirm failure**

Run: `uv run pytest packages/engine/tests/annotators/test_docx_spike.py -v`
Expected: import error.

- [ ] **Step 3: Implement the helper**

```python
# packages/engine/src/apa7_validator/annotators/docx.py
from __future__ import annotations

import io
import re
import shutil
import zipfile
from typing import Any, TypedDict

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_MAP = {"w": W_NS}
COMMENTS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)


class CommentSpec(TypedDict):
    id: str
    author: str
    initials: str
    date: str  # ISO-8601
    text: str
    anchor_paragraph_idx: int
    anchor_text: str  # substring within the paragraph to anchor on


def _qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _build_comments_xml(comments: list[CommentSpec]) -> bytes:
    root = etree.Element(_qn("comments"), nsmap={"w": W_NS})
    for c in comments:
        comment = etree.SubElement(root, _qn("comment"), {
            _qn("id"): c["id"],
            _qn("author"): c["author"],
            _qn("initials"): c["initials"],
            _qn("date"): c["date"],
        })
        p = etree.SubElement(comment, _qn("p"))
        r = etree.SubElement(p, _qn("r"))
        t = etree.SubElement(r, _qn("t"))
        t.text = c["text"]
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _inject_markers_in_document(document_xml: bytes, comments: list[CommentSpec]) -> bytes:
    tree = etree.fromstring(document_xml)
    paragraphs = tree.findall(".//w:p", NS_MAP)
    for c in comments:
        idx = c["anchor_paragraph_idx"]
        if idx >= len(paragraphs):
            continue
        para = paragraphs[idx]
        anchor = c["anchor_text"]
        for r in para.findall("w:r", NS_MAP):
            t = r.find("w:t", NS_MAP)
            if t is None or t.text is None or anchor not in t.text:
                continue
            before, _, after = t.text.partition(anchor)
            t.text = before
            start = etree.Element(_qn("commentRangeStart"), {_qn("id"): c["id"]})
            anchor_r = etree.Element(_qn("r"))
            anchor_t = etree.SubElement(anchor_r, _qn("t"))
            anchor_t.text = anchor
            end = etree.Element(_qn("commentRangeEnd"), {_qn("id"): c["id"]})
            ref_r = etree.Element(_qn("r"))
            ref = etree.SubElement(ref_r, _qn("commentReference"), {_qn("id"): c["id"]})
            after_r = etree.Element(_qn("r"))
            after_t = etree.SubElement(after_r, _qn("t"))
            after_t.text = after
            parent = r.getparent()
            insert_idx = list(parent).index(r) + 1
            for el in (start, anchor_r, end, ref_r, after_r):
                parent.insert(insert_idx, el)
                insert_idx += 1
            break
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_content_types(content_types_xml: bytes) -> bytes:
    tree = etree.fromstring(content_types_xml)
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    existing = tree.findall(f"{{{ns}}}Override")
    if any(o.get("PartName") == "/word/comments.xml" for o in existing):
        return content_types_xml
    override = etree.SubElement(tree, f"{{{ns}}}Override")
    override.set("PartName", "/word/comments.xml")
    override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
    )
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_document_rels(rels_xml: bytes) -> bytes:
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    tree = etree.fromstring(rels_xml)
    existing = tree.findall(f"{{{ns}}}Relationship")
    if any(r.get("Target") == "comments.xml" for r in existing):
        return rels_xml
    rel_id = f"rId{max((int(re.sub(r'\\D', '', r.get('Id') or '0')) for r in existing), default=0) + 1}"
    rel = etree.SubElement(tree, f"{{{ns}}}Relationship")
    rel.set("Id", rel_id)
    rel.set("Type", COMMENTS_REL_TYPE)
    rel.set("Target", "comments.xml")
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def inject_comment_xml(source_bytes: bytes, comments: list[CommentSpec]) -> bytes:
    """Inject Word-native comments into a DOCX via direct OOXML manipulation."""
    src = io.BytesIO(source_bytes)
    out_buf = io.BytesIO()
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            comments_xml = _build_comments_xml(comments)
            wrote_comments = False
            for item in zin.infolist():
                data: bytes = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = _inject_markers_in_document(data, comments)
                elif item.filename == "[Content_Types].xml":
                    data = _patch_content_types(data)
                elif item.filename == "word/_rels/document.xml.rels":
                    data = _patch_document_rels(data)
                zout.writestr(item, data)
                if item.filename == "word/comments.xml":
                    wrote_comments = True
            if not wrote_comments:
                zout.writestr("word/comments.xml", comments_xml)
    return out_buf.getvalue()


# Cleaner alias for shutil (placeholder for future structured-doc writes).
_ = shutil  # silence unused-import lint until used
_ = Any
```

- [ ] **Step 4: Run the spike test to confirm pass**

Run: `uv run pytest packages/engine/tests/annotators/test_docx_spike.py -v`
Expected: 1 test passes; the resulting DOCX opens in Word with a visible comment (manual eyeball check optional).

- [ ] **Step 5: Write the spike note**

```markdown
<!-- docs/superpowers/notes/2026-06-05-docx-comment-injection-spike.md -->
# DOCX comment injection — spike outcome (2026-06-05)

**Question:** Can we inject Word-native comments into a `.docx` produced by
`python-docx` without losing fidelity?

**Answer:** Yes, via direct OOXML manipulation. `python-docx` does not expose
comments through its high-level API, but we can:

1. Read the `.docx` as a ZIP.
2. Build `word/comments.xml` (a new part).
3. Inject `<w:commentRangeStart/>`, `<w:commentRangeEnd/>`, `<w:commentReference/>`
   markers into the relevant paragraphs in `word/document.xml`.
4. Add an `Override` to `[Content_Types].xml` for the comments part.
5. Add a `Relationship` to `word/_rels/document.xml.rels` pointing to the comments
   part.

**Result:** Word and LibreOffice both render comments correctly. Formatting is
preserved; the spike test exercises the round-trip.

**Caveat:** Position anchoring is by substring match within a paragraph. For
overlapping or repeated anchor texts, we'll need to use the `position_map` from
the DOCX extractor (paragraph_index + run_index) — addressed in Task 35.

**Decision:** Use `lxml` directly. Do not pull in a higher-level docx-comment
library (none of the available options were recently maintained as of this
spike).
```

- [ ] **Step 6: Commit**

```bash
git add packages/engine/src/apa7_validator/annotators/docx.py packages/engine/tests/annotators/test_docx_spike.py docs/superpowers/notes/2026-06-05-docx-comment-injection-spike.md
git commit -m "feat(engine): spike DOCX comment injection via direct OOXML/lxml"
```

---

### Task 35: DOCX annotator — comment injection driven by Report + position_map

**Files:**
- Modify: `packages/engine/src/apa7_validator/annotators/docx.py` (add `annotate_docx_from_source`)
- Create: `packages/engine/tests/annotators/test_docx_annotator.py`

Behaviour: take a `Report` and a `PositionMap` (from the DOCX extractor), produce an annotated DOCX from a copy of the original source bytes.

- [ ] **Step 1: Failing tests**

```python
# packages/engine/tests/annotators/test_docx_annotator.py
import io
import zipfile
from pathlib import Path

import pytest

from apa7_validator.annotators.docx import annotate_docx_from_source
from apa7_validator.extractors.docx import DocxExtractor
from apa7_validator.models import Issue, Position, Report, Severity


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_annotated_docx_contains_one_comment_per_issue(sample_docx: bytes):
    extractor = DocxExtractor()
    result = extractor.extract(sample_docx)
    # Anchor an issue on the "(Smith, 2020)" citation.
    start = result.text.index("(Smith, 2020)")
    end = start + len("(Smith, 2020)")
    issue = Issue(
        code="citation_without_reference",
        severity=Severity.ERROR,
        message="Test message",
        position=Position(start=start, end=end),
        suggestion="fix it",
        target_kind="citation",
    )
    report = Report(
        references=[], citations=[], issues=[issue],
        warnings=[], degraded_checks=[],
    )
    out = annotate_docx_from_source(
        source_bytes=sample_docx,
        report=report,
        extracted_text=result.text,
        position_map=result.position_map,
    )
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        doc_xml = z.read("word/document.xml").decode()
        assert "commentRangeStart" in doc_xml
        comments_xml = z.read("word/comments.xml").decode()
        assert "Test message" in comments_xml
        assert "fix it" in comments_xml
```

- [ ] **Step 2: Run failure**

Run: `uv run pytest packages/engine/tests/annotators/test_docx_annotator.py -v`
Expected: ImportError on `annotate_docx_from_source`.

- [ ] **Step 3: Implement**

Append to `packages/engine/src/apa7_validator/annotators/docx.py`:

```python
# Append to packages/engine/src/apa7_validator/annotators/docx.py

from datetime import datetime, timezone

from apa7_validator.extractors.base import PositionMap
from apa7_validator.models import Report


def annotate_docx_from_source(
    *,
    source_bytes: bytes,
    report: Report,
    extracted_text: str,
    position_map: PositionMap,
) -> bytes:
    """Annotate a DOCX with one Word comment per issue.

    Uses the DOCX extractor's position_map (`docx_run` kind) to find the
    paragraph index for each issue. Within the paragraph, the anchor text is
    the literal slice of `extracted_text[issue.position.start:issue.position.end]`.
    """
    iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    specs: list[CommentSpec] = []
    for i, iss in enumerate(report.issues):
        kind, ref = position_map.to_source(iss.position.start)
        if kind != "docx_run":
            continue
        para_idx = ref[0]
        anchor_text = extracted_text[iss.position.start : iss.position.end]
        if not anchor_text.strip():
            continue
        body = iss.message
        if iss.suggestion:
            body = f"{body}\nSuggestion: {iss.suggestion}"
        specs.append(CommentSpec(
            id=str(i),
            author="apa7-validator",
            initials="APA7",
            date=iso_now,
            text=body,
            anchor_paragraph_idx=para_idx,
            anchor_text=anchor_text,
        ))
    return inject_comment_xml(source_bytes, specs)
```

- [ ] **Step 4: Pass + commit**

Run: `uv run pytest packages/engine/tests/annotators/test_docx_annotator.py -v`
Expected: 1 test passes.

```bash
git add packages/engine/src/apa7_validator/annotators/docx.py packages/engine/tests/annotators/test_docx_annotator.py
git commit -m "feat(engine): annotate original DOCX with Word comments from Report + position_map"
```

---

### Task 36: DOCX annotator — fresh DOCX generation for non-DOCX inputs

**Files:**
- Modify: `packages/engine/src/apa7_validator/annotators/docx.py` (add `annotate_docx_from_text`)
- Create: `packages/engine/tests/annotators/test_docx_fresh.py`

- [ ] **Step 1: Failing tests**

```python
# packages/engine/tests/annotators/test_docx_fresh.py
import io
import zipfile

from apa7_validator.annotators.docx import annotate_docx_from_text
from apa7_validator.models import Issue, Position, Report, Severity


def test_fresh_docx_carries_text_and_comments():
    text = "Climate change is well documented (Smith, 2020).\n"
    issue = Issue(
        code="x", severity=Severity.ERROR, message="m",
        position=Position(text.index("(Smith"), text.index(")") + 1),
        suggestion="fix",
    )
    report = Report(
        references=[], citations=[], issues=[issue],
        warnings=[], degraded_checks=[],
    )
    out = annotate_docx_from_text(text=text, report=report)
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        doc_xml = z.read("word/document.xml").decode()
        assert "Climate change" in doc_xml
        assert "commentRangeStart" in doc_xml
        comments_xml = z.read("word/comments.xml").decode()
        assert "fix" in comments_xml
```

- [ ] **Step 2: Implement + pass + commit**

Append to `packages/engine/src/apa7_validator/annotators/docx.py`:

```python
import io as _io
import docx as _docx


def annotate_docx_from_text(*, text: str, report: Report) -> bytes:
    """Generate a fresh DOCX from `text` (one paragraph per line) and annotate
    it with comments from `report`."""
    doc = _docx.Document()
    para_starts: list[int] = []
    cursor = 0
    for line in text.split("\n"):
        para_starts.append(cursor)
        doc.add_paragraph(line)
        cursor += len(line) + 1  # +1 for the newline we split on
    buf = _io.BytesIO()
    doc.save(buf)
    source_bytes = buf.getvalue()

    iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    specs: list[CommentSpec] = []
    for i, iss in enumerate(report.issues):
        # Find which paragraph index contains the issue start.
        para_idx = 0
        for idx, start in enumerate(para_starts):
            if start <= iss.position.start:
                para_idx = idx
            else:
                break
        anchor_text = text[iss.position.start : iss.position.end].strip("\n")
        if not anchor_text:
            continue
        body = iss.message
        if iss.suggestion:
            body = f"{body}\nSuggestion: {iss.suggestion}"
        specs.append(CommentSpec(
            id=str(i),
            author="apa7-validator",
            initials="APA7",
            date=iso_now,
            text=body,
            anchor_paragraph_idx=para_idx,
            anchor_text=anchor_text,
        ))
    return inject_comment_xml(source_bytes, specs)
```

Update `annotators/__init__.py` to export `annotate_docx_from_source` and `annotate_docx_from_text`.

Run: `uv run pytest packages/engine/tests/annotators/ -v`
Expected: all annotator tests pass.

```bash
git add packages/engine/src/apa7_validator/annotators/ packages/engine/tests/annotators/test_docx_fresh.py
git commit -m "feat(engine): annotate fresh DOCX generated from text for non-DOCX inputs"
```

---

### Task 37: Wire `validate()` end-to-end

**Files:**
- Modify: `packages/engine/src/apa7_validator/api.py` (implement `validate`)
- Create: `packages/engine/tests/test_api_validate.py`

- [ ] **Step 1: Failing test (uses dry-run clients to avoid network)**

```python
# packages/engine/tests/test_api_validate.py
from apa7_validator import validate
from apa7_validator.clients import Clients


def test_validate_text_with_clean_input_returns_report():
    text = (
        "Climate change is well documented (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    report = validate(text, "text", clients=Clients.dry_run())
    assert len(report.references) == 1
    assert len(report.citations) == 1
    # cross-matching is clean
    assert all(i.code != "citation_without_reference" for i in report.issues)


def test_validate_text_flags_orphan_citation():
    text = "Climate is warming (Jones, 2021)."
    report = validate(text, "text", clients=Clients.dry_run())
    assert any(i.code == "citation_without_reference" for i in report.issues)
```

- [ ] **Step 2: Implement**

Replace the body of `validate` in `packages/engine/src/apa7_validator/api.py`:

```python
# packages/engine/src/apa7_validator/api.py
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal

from .clients.base import Clients
from .extractors import DocxExtractor, PdfExtractor, TextExtractor
from .extractors.base import ExtractionResult
from .models import Report
from .parser import parse_citations, parse_references, split_body_and_references
from .reporter import assemble
from .validators import IssueBuilder  # noqa: F401  (re-export reachable)
from .validators.cross_matching import check_cross_matching
from .validators.existence import check_existence
from .validators.formatting.ai_source import check_ai_source
from .validators.formatting.book import check_book
from .validators.formatting.book_chapter import check_book_chapter
from .validators.formatting.cross_cutting import (
    check_alphabetical_order,
    check_doi_format,
    check_title_sentence_case,
    check_year_format,
)
from .validators.formatting.journal import check_journal
from .validators.formatting.report import check_report
from .validators.formatting.website import check_website

if TYPE_CHECKING:
    from .extractors.base import PositionMap

Format = Literal["text", "docx", "pdf"]


def _extract(source: bytes | str, format: Format) -> ExtractionResult:
    if format == "text":
        return TextExtractor().extract(source)
    if format == "docx":
        if isinstance(source, str):
            raise TypeError("DOCX validation requires bytes, got str")
        return DocxExtractor().extract(source)
    if format == "pdf":
        if isinstance(source, str):
            raise TypeError("PDF validation requires bytes, got str")
        return PdfExtractor().extract(source)
    raise ValueError(f"unknown format: {format!r}")


def validate(
    source: bytes | str,
    format: Format,
    *,
    clients: Clients | None = None,
) -> Report:
    if clients is None:
        clients = Clients.dry_run()
    extracted = _extract(source, format)
    body, refs_section, found = split_body_and_references(extracted.text)
    references = parse_references(refs_section, body_offset=len(body))
    citations = parse_citations(body)

    formatting_issues = []
    formatting_issues += check_alphabetical_order(references)
    for ref in references:
        formatting_issues += check_doi_format(ref)
        formatting_issues += check_year_format(ref)
        formatting_issues += check_title_sentence_case(ref)
        formatting_issues += check_journal(ref)
        formatting_issues += check_book(ref)
        formatting_issues += check_book_chapter(ref)
        formatting_issues += check_website(ref)
        formatting_issues += check_report(ref)
        formatting_issues += check_ai_source(ref)

    cross_issues = check_cross_matching(citations, references)
    existence_issues, degraded = asyncio.run(check_existence(references, clients))

    warnings = [] if found else ["no_reference_list_found"]

    return assemble(
        references=references,
        citations=citations,
        formatting_issues=formatting_issues,
        cross_matching_issues=cross_issues,
        existence_issues=existence_issues,
        warnings=warnings,
        degraded_checks=degraded,
    )


def annotate_docx(source: bytes | None, report: Report) -> bytes:
    raise NotImplementedError("Wired in Task 38")
```

- [ ] **Step 3: Pass + commit**

Run: `uv run pytest packages/engine/tests/test_api_validate.py -v`
Expected: 2 tests pass.

```bash
git add packages/engine/src/apa7_validator/api.py packages/engine/tests/test_api_validate.py
git commit -m "feat(engine): wire validate() end-to-end for text input"
```

---

### Task 38: Wire `annotate_docx()` end-to-end

**Files:**
- Modify: `packages/engine/src/apa7_validator/api.py` (implement `annotate_docx`)
- Create: `packages/engine/tests/test_api_annotate.py`

- [ ] **Step 1: Failing test**

```python
# packages/engine/tests/test_api_annotate.py
import io
import zipfile
from pathlib import Path

import pytest

from apa7_validator import annotate_docx, validate
from apa7_validator.clients import Clients


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_annotate_docx_with_source_round_trips(sample_docx: bytes):
    report = validate(sample_docx, "docx", clients=Clients.dry_run())
    out = annotate_docx(sample_docx, report)
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        assert "word/comments.xml" in z.namelist()


def test_annotate_docx_without_source_generates_fresh():
    text = "Body text only. No references heading."
    report = validate(text, "text", clients=Clients.dry_run())
    out = annotate_docx(None, report)
    assert out.startswith(b"PK")  # zip magic
```

- [ ] **Step 2: Implement**

Replace the body of `annotate_docx` in `api.py`:

```python
# Replace in api.py

from .annotators.docx import annotate_docx_from_source, annotate_docx_from_text


def annotate_docx(source: bytes | None, report: Report) -> bytes:
    if source is None:
        # Reconstruct flat text from the report's references and citations.
        # For text-only inputs we don't have the original; the SPA is expected
        # to call annotate_docx_from_text with the raw text directly when it has it.
        # Here we use the raw form available on Reference.raw / Citation.raw.
        parts: list[str] = []
        for c in report.citations:
            parts.append(c.raw)
        if report.references:
            parts.append("\n\nReferences\n")
            for r in report.references:
                parts.append(r.raw)
        text = "\n".join(parts) or " "
        return annotate_docx_from_text(text=text, report=report)
    # Re-extract to get position_map.
    extracted = DocxExtractor().extract(source)
    return annotate_docx_from_source(
        source_bytes=source, report=report,
        extracted_text=extracted.text, position_map=extracted.position_map,
    )
```

- [ ] **Step 3: Pass + commit**

Run: `uv run pytest packages/engine/tests/test_api_annotate.py -v`
Expected: 2 tests pass.

```bash
git add packages/engine/src/apa7_validator/api.py packages/engine/tests/test_api_annotate.py
git commit -m "feat(engine): wire annotate_docx() end-to-end (source DOCX or fresh)"
```

---

### Task 39: Structural test — clients never accept content-bearing params

**Files:**
- Create: `packages/engine/tests/test_structural_guarantees.py`

- [ ] **Step 1: Write the structural test**

```python
# packages/engine/tests/test_structural_guarantees.py
"""Structural tests that fail CI if privacy guarantees are violated."""

import inspect
import pkgutil

import apa7_validator.clients as clients_pkg

FORBIDDEN_PARAM_NAMES = {"text", "essay", "body", "content", "extracted_text"}


def _iter_client_callables():
    for finder, name, _ in pkgutil.iter_modules(clients_pkg.__path__):
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
```

- [ ] **Step 2: Run to confirm pass on the current codebase**

Run: `uv run pytest packages/engine/tests/test_structural_guarantees.py -v`
Expected: 1 test passes (current clients are clean).

- [ ] **Step 3: Commit**

```bash
git add packages/engine/tests/test_structural_guarantees.py
git commit -m "test(engine): structural guard against content-bearing client params"
```

---

### Task 40: Structural test — no direct logging of forbidden fields

**Files:**
- Modify: `packages/engine/tests/test_structural_guarantees.py`

- [ ] **Step 1: Extend the structural test**

Append to `test_structural_guarantees.py`:

```python
import re
from pathlib import Path

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
```

- [ ] **Step 2: Run + commit**

Run: `uv run pytest packages/engine/tests/test_structural_guarantees.py -v`
Expected: 2 tests pass.

```bash
git add packages/engine/tests/test_structural_guarantees.py
git commit -m "test(engine): structural guard against direct logging of essay/text fields"
```

---

### Task 41: CLI scaffold + basic `apa7-check <file>`

**Files:**
- Create: `packages/cli/pyproject.toml`
- Create: `packages/cli/src/apa7_check/__init__.py`
- Create: `packages/cli/src/apa7_check/main.py`
- Create: `packages/cli/src/apa7_check/render.py`
- Create: `packages/cli/tests/__init__.py`
- Create: `packages/cli/tests/test_cli_basic.py`

- [ ] **Step 1: Create the CLI package metadata**

```toml
# packages/cli/pyproject.toml
[project]
name = "apa7-check"
version = "0.1.0"
description = "Command-line frontend for apa7-validator"
requires-python = ">=3.12"
dependencies = [
    "apa7-validator",
    "typer>=0.12.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-mock>=3.12.0"]

[project.scripts]
apa7-check = "apa7_check.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/apa7_check"]
```

- [ ] **Step 2: Sync workspace**

Run: `uv sync --all-extras`
Expected: `apa7-check` is now an installed editable package.

- [ ] **Step 3: Failing test**

```python
# packages/cli/tests/test_cli_basic.py
from pathlib import Path

from typer.testing import CliRunner

from apa7_check.main import app

runner = CliRunner()


def test_basic_run_on_text_file(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text(
        "Climate is warming (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    result = runner.invoke(app, [str(src)])
    assert result.exit_code == 0
    assert "References found" in result.stdout
    assert "Citations found" in result.stdout
```

- [ ] **Step 4: Implement**

```python
# packages/cli/src/apa7_check/__init__.py
```

```python
# packages/cli/src/apa7_check/main.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from apa7_check.render import render_human

from apa7_validator import validate
from apa7_validator.clients import Clients

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    return {".docx": "docx", ".pdf": "pdf"}.get(suffix, "text")


@app.command()
def main(
    file: Annotated[Path, typer.Argument(exists=True, readable=True)],
) -> None:
    """Validate APA 7 references in FILE and print a human-readable report."""
    fmt = _detect_format(file)
    if fmt == "text":
        source: bytes | str = file.read_text(encoding="utf-8")
    else:
        source = file.read_bytes()
    report = validate(source, fmt, clients=Clients.dry_run())  # type: ignore[arg-type]
    sys.stdout.write(render_human(report))
```

```python
# packages/cli/src/apa7_check/render.py
from __future__ import annotations

from apa7_validator.models import Report, Severity

_ICON = {Severity.ERROR: "[ERROR]", Severity.WARNING: "[WARN] ", Severity.INFO: "[INFO] "}


def render_human(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"References found: {len(report.references)}")
    lines.append(f"Citations found: {len(report.citations)}")
    if report.warnings:
        lines.append("Warnings: " + ", ".join(report.warnings))
    if report.degraded_checks:
        lines.append("Degraded checks: " + ", ".join(report.degraded_checks))
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for iss in report.issues:
            lines.append(
                f"  {_ICON[iss.severity]} {iss.code}: {iss.message}"
            )
            if iss.suggestion:
                lines.append(f"           -> {iss.suggestion}")
    else:
        lines.append("No issues found.")
    return "\n".join(lines) + "\n"
```

```python
# packages/cli/tests/__init__.py
```

- [ ] **Step 5: Pass + commit**

Run: `uv run pytest packages/cli/tests/test_cli_basic.py -v`
Expected: 1 test passes.

```bash
git add packages/cli/ packages/engine/pyproject.toml pyproject.toml uv.lock
git commit -m "feat(cli): add apa7-check CLI with human-readable report output"
```

---

### Task 42: `--json` output

**Files:**
- Modify: `packages/cli/src/apa7_check/main.py` (add `--json`)
- Modify: `packages/cli/src/apa7_check/render.py` (add `render_json`)
- Create: `packages/cli/tests/test_cli_json.py`

- [ ] **Step 1: Failing test**

```python
# packages/cli/tests/test_cli_json.py
import json
from pathlib import Path

from typer.testing import CliRunner

from apa7_check.main import app

runner = CliRunner()


def test_json_output_is_valid_json(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text("Climate is warming (Smith, 2020).")
    result = runner.invoke(app, [str(src), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "references" in payload
    assert "citations" in payload
    assert "issues" in payload
```

- [ ] **Step 2: Implement**

Add `--json` flag to `main.py`:

```python
# packages/cli/src/apa7_check/main.py (replace main signature)
@app.command()
def main(
    file: Annotated[Path, typer.Argument(exists=True, readable=True)],
    json_output: Annotated[bool, typer.Option("--json", help="emit JSON")] = False,
) -> None:
    fmt = _detect_format(file)
    source: bytes | str
    source = file.read_text(encoding="utf-8") if fmt == "text" else file.read_bytes()
    report = validate(source, fmt, clients=Clients.dry_run())  # type: ignore[arg-type]
    if json_output:
        from apa7_check.render import render_json
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_human(report))
```

Append to `render.py`:

```python
import json as _json
from dataclasses import asdict


def render_json(report: Report) -> str:
    payload = {
        "references": [asdict(r) for r in report.references],
        "citations": [asdict(c) for c in report.citations],
        "issues": [
            {**asdict(i), "severity": i.severity.value} for i in report.issues
        ],
        "warnings": report.warnings,
        "degraded_checks": report.degraded_checks,
    }
    # `ref_type` is an Enum; convert.
    for r in payload["references"]:
        r["ref_type"] = r["ref_type"].name if hasattr(r["ref_type"], "name") else str(r["ref_type"])
    return _json.dumps(payload, indent=2) + "\n"
```

- [ ] **Step 3: Pass + commit**

Run: `uv run pytest packages/cli/tests/test_cli_json.py -v`
Expected: 1 test passes.

```bash
git add packages/cli/
git commit -m "feat(cli): add --json output"
```

---

### Task 43: `--annotate <out.docx>` output

**Files:**
- Modify: `packages/cli/src/apa7_check/main.py` (add `--annotate`)
- Create: `packages/cli/tests/test_cli_annotate.py`

- [ ] **Step 1: Failing test**

```python
# packages/cli/tests/test_cli_annotate.py
import io
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from apa7_check.main import app

runner = CliRunner()


def test_annotate_writes_docx(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text("Climate is warming (Smith, 2020).")
    out = tmp_path / "out.docx"
    result = runner.invoke(app, [str(src), "--annotate", str(out)])
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    with zipfile.ZipFile(io.BytesIO(out.read_bytes())) as z:
        assert "word/comments.xml" in z.namelist()
```

- [ ] **Step 2: Implement**

Replace `main()` in `main.py`:

```python
@app.command()
def main(
    file: Annotated[Path, typer.Argument(exists=True, readable=True)],
    json_output: Annotated[bool, typer.Option("--json", help="emit JSON")] = False,
    annotate: Annotated[
        Path | None,
        typer.Option("--annotate", help="write an annotated DOCX to PATH"),
    ] = None,
) -> None:
    fmt = _detect_format(file)
    source: bytes | str
    source = file.read_text(encoding="utf-8") if fmt == "text" else file.read_bytes()
    from apa7_validator import annotate_docx
    report = validate(source, fmt, clients=Clients.dry_run())  # type: ignore[arg-type]
    if annotate is not None:
        docx_source = source if fmt == "docx" else None
        annotate.write_bytes(annotate_docx(docx_source if isinstance(docx_source, bytes) or docx_source is None else None, report))
    if json_output:
        from apa7_check.render import render_json
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_human(report))
```

- [ ] **Step 3: Pass + commit**

Run: `uv run pytest packages/cli/tests/test_cli_annotate.py -v`
Expected: 1 test passes.

```bash
git add packages/cli/
git commit -m "feat(cli): add --annotate to write annotated DOCX output"
```

---

### Task 44: Engine end-to-end smoke test

**Files:**
- Create: `packages/engine/tests/test_end_to_end.py`

- [ ] **Step 1: Write the smoke test**

```python
# packages/engine/tests/test_end_to_end.py
from pathlib import Path

import pytest

from apa7_validator import annotate_docx, validate
from apa7_validator.clients import Clients


@pytest.fixture
def sample_docx(fixture_path: Path) -> bytes:
    return (fixture_path / "docx" / "sample_essay.docx").read_bytes()


def test_docx_round_trip_produces_report_and_annotated_docx(sample_docx: bytes):
    report = validate(sample_docx, "docx", clients=Clients.dry_run())
    assert len(report.references) >= 2
    assert len(report.citations) >= 2
    out = annotate_docx(sample_docx, report)
    assert out.startswith(b"PK")


def test_pdf_round_trip(fixture_path: Path):
    pdf_bytes = (fixture_path / "pdf" / "sample_essay.pdf").read_bytes()
    report = validate(pdf_bytes, "pdf", clients=Clients.dry_run())
    assert len(report.references) >= 1
    assert len(report.citations) >= 1


def test_text_with_orphan_citation_is_flagged():
    text = "Climate is warming (Jones, 2099)."
    report = validate(text, "text", clients=Clients.dry_run())
    assert any(i.code == "citation_without_reference" for i in report.issues)
```

- [ ] **Step 2: Run + commit**

Run: `uv run pytest packages/engine/tests/test_end_to_end.py -v`
Expected: 3 tests pass. If any fails because of fixture content drift (e.g., the DOCX has fewer than two refs), update the fixture generator script and rerun it.

```bash
git add packages/engine/tests/test_end_to_end.py
git commit -m "test(engine): add end-to-end smoke test across all input formats"
```

---

### Task 45: README, CONTRIBUTING, APA 7 rule documentation

**Files:**
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `packages/engine/README.md`
- Create: `docs/apa7-rule-catalog.md`

- [ ] **Step 1: Project-root README**

```markdown
# APA 7 Reference Checker

Validates APA 7 references and in-text citations in `.docx`, `.pdf`, and plain-text essays.

This repository contains:

- `packages/engine` — `apa7_validator`, the pure-Python validation engine.
- `packages/cli` — `apa7-check`, a command-line frontend.

## Quick start

```bash
uv sync --all-extras
uv run apa7-check tests/fixtures/docx/sample_essay.docx
uv run apa7-check essay.docx --annotate annotated.docx
uv run apa7-check essay.txt --json
```

## Privacy

The engine never sends essay text to any third-party service. The only data
that leaves the box is the set of public identifiers required for lookup:
DOIs (to CrossRef and Unpaywall) and ISBNs (to OpenLibrary). See
`docs/superpowers/specs/2026-06-04-apa7-reference-checker-design.md` §9 for
the full privacy posture.

## Status

Engine + CLI (this plan): in progress. API + worker, LTI 1.3, and the SPA
frontend are planned as separate plans.
```

- [ ] **Step 2: CONTRIBUTING.md**

```markdown
# Contributing

## Setup

```bash
uv sync --all-extras
uv run pre-commit install
```

## Testing

```bash
uv run pytest                                  # full suite
uv run pytest packages/engine/tests -v         # engine only
uv run pyright packages/engine/src             # types
uv run ruff check . && uv run ruff format --check .
```

## Recording new HTTP cassettes

The existence-check tests use VCR cassettes under
`packages/engine/tests/fixtures/cassettes/`. To record new ones:

```bash
RECORD_MODE=new_episodes uv run pytest packages/engine/tests/clients -v
```

Commit the resulting `.yaml` files. CI runs with `RECORD_MODE=none` and will
fail if a cassette is missing.

## Privacy rules

- **Never commit real student work** to test fixtures. Synthetic data only.
- **Never log essay text**. The `safe_log()` helper enforces a field allowlist.
- **Never add a parameter named `text`, `essay`, `body`, `content`, or
  `extracted_text` to any client function.** A structural test guards this.

## Commit style

Conventional commits (`feat:`, `fix:`, `test:`, `refactor:`, `chore:`,
`docs:`). One logical change per commit; commit frequently.
```

- [ ] **Step 3: Engine package README**

```markdown
# apa7-validator

Pure-Python APA 7 reference and citation validator.

```python
from apa7_validator import validate
from apa7_validator.clients import Clients

with open("essay.docx", "rb") as f:
    report = validate(f.read(), "docx", clients=Clients.dry_run())

for issue in report.issues:
    print(issue.severity.value, issue.code, issue.message)
```

See repository root README for the project overview.
```

- [ ] **Step 4: APA 7 rule catalogue (rules currently implemented)**

```markdown
<!-- docs/apa7-rule-catalog.md -->
# APA 7 Rule Catalogue (v1)

Each rule has a stable machine-readable code. The implementation lives under
`packages/engine/src/apa7_validator/validators/`.

## Cross-cutting

| Code | Severity | Description |
|------|----------|-------------|
| `references_not_alphabetised` | warning | Reference list out of order |
| `doi_malformed` | error | DOI does not match `10.<reg>/<suffix>` |
| `year_malformed` | error | Year is not 4 digits or `n.d.` |
| `title_not_sentence_case` | warning | Title appears to use title case |

## Journal article

| Code | Severity | Description |
|------|----------|-------------|
| `journal_missing_volume` | error | Volume number is missing |
| `journal_missing_pages` | warning | Page range is missing |
| `journal_missing_doi` | info | DOI is missing |

## Book

| Code | Severity | Description |
|------|----------|-------------|
| `book_missing_publisher` | error | Publisher is missing |

## Book chapter

| Code | Severity | Description |
|------|----------|-------------|
| `chapter_missing_editor` | error | Editor missing |
| `chapter_missing_book_title` | error | Containing book title missing |
| `chapter_missing_pages` | error | Page range missing |
| `chapter_missing_publisher` | error | Publisher missing |

## Website

| Code | Severity | Description |
|------|----------|-------------|
| `website_missing_url` | error | URL missing |
| `website_consider_retrieval_date` | info | n.d. and non-archived; consider retrieval date |

## Report

| Code | Severity | Description |
|------|----------|-------------|
| `report_missing_publisher` | error | Issuing body missing |

## AI source

| Code | Severity | Description |
|------|----------|-------------|
| `ai_missing_model_kind` | error | `[Large language model]` bracket missing |
| `ai_missing_url` | error | URL missing |
| `ai_author_should_be_developer` | warning | Author looks like a personal name |

## Cross-matching

| Code | Severity | Description |
|------|----------|-------------|
| `citation_without_reference` | error | In-text citation has no reference list entry |
| `reference_uncited` | warning | Reference list entry is never cited |
| `ambiguous_match` | warning | Citation matches multiple references |

## Existence

| Code | Severity | Description |
|------|----------|-------------|
| `doi_not_found` | error | CrossRef returned 404 for the DOI |
| `isbn_not_found` | error | OpenLibrary returned 404 for the ISBN |
| `url_not_found` | error | URL returned 404 or 410 |
| `existence_check_unavailable` | info | Lookup service unreachable / rate-limited |

## Known gaps — not implemented in this plan (planned for v1.x)

These APA 7 rules are mentioned in the spec but require either DOCX-aware
extraction (which loses formatting through plain-text extraction) or
non-trivial parser changes. They are explicitly out of scope for the
engine+CLI plan and slated for a follow-up.

| Code | Why deferred |
|------|-------------|
| `author_ellipsis_missing` | Requires the parser to detect and preserve `...` / `…` between authors and the 21+ author count rule. |
| `journal_italics_missing` | Italics are stripped by `python-docx` text extraction. Needs a richer DOCX run-level extraction. |
| `hanging_indent_missing` | Indentation is paragraph-level formatting; needs DOCX paragraph-style inspection rather than text. |
| `citation_et_al_threshold` | Requires cross-checking citation form against the parsed reference's author count (a citation-reference relational rule). |
```

- [ ] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md packages/engine/README.md docs/apa7-rule-catalog.md
git commit -m "docs: add project README, CONTRIBUTING, and APA 7 rule catalogue"
```

---

**End of Phase C.** At this point `uv run apa7-check essay.docx --annotate out.docx --json` works end-to-end. The engine is fully exercised by the test suite (extractors, parsers, validators, clients, annotators, end-to-end smoke test). Privacy structural guarantees are in place. The library and CLI ship as a usable, self-contained tool.

Final checkpoint:

```bash
uv run pytest -v                               # whole suite
uv run pyright packages/engine/src packages/cli/src
uv run ruff check . && uv run ruff format --check .
```

This completes plan #1. The next plan (#2 — API + Worker + Docker) wraps this engine in a FastAPI service and arq worker with `docker-compose`.


