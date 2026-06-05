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
    extras: dict[str, str] = field(default_factory=lambda: {})


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
