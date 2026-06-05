"""Public API of the validator engine.

The actual implementations are wired in Task 37 (validate) and Task 38
(annotate_docx). This module defines the stable surface area.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .models import Report

if TYPE_CHECKING:
    # Clients is defined in Task 25.  Until that module exists, alias to Any so
    # pyright sees a concrete type rather than Unknown.
    Clients = Any

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
    raise NotImplementedError("Wired in Task 38")
