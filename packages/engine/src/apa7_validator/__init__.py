"""APA 7 reference and citation validator."""

from .api import Format, annotate_docx, validate, validate_async
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
    "validate_async",
]
