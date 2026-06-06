from __future__ import annotations

import re

from ...models import Issue, Position, Reference
from ..base import IssueBuilder

_REF_BUILDER = IssueBuilder(target_kind="reference")
_GLOBAL_BUILDER = IssueBuilder(target_kind="global")

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_YEAR_RE = re.compile(r"^(?:\d{4}[a-z]?|n\.d\.(?:-[a-z])?)$")
_DEPRECATED_DOI_PREFIX_RE = re.compile(r"\bdoi:\s*10\.", re.IGNORECASE)


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
    issues: list[Issue] = []
    if ref.doi is not None and not _DOI_RE.match(ref.doi):
        issues.append(
            _REF_BUILDER.error(
                code="doi_malformed",
                message=f"DOI '{ref.doi}' is not in the expected '10.<registrant>/<suffix>' form",
                position=ref.position,
                suggestion="Format DOIs as 'https://doi.org/10.xxxx/yyyy' with the bare DOI starting '10.'",
            )
        )
    if _DEPRECATED_DOI_PREFIX_RE.search(ref.raw):
        issues.append(
            _REF_BUILDER.warning(
                code="doi_surface_form_deprecated",
                message="DOI uses deprecated 'doi:' prefix; APA 7 expects 'https://doi.org/...'",
                position=ref.position,
                suggestion="Replace 'doi:10.xxxx/yyyy' with 'https://doi.org/10.xxxx/yyyy'",
            )
        )
    return issues


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
    # First word capitalised, others lowercase except after a colon or period, or proper nouns.
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


# ---------------------------------------------------------------------------
# Source-count threshold
# ---------------------------------------------------------------------------

# Many first-year courses require 10+ sources.
# The threshold is fixed in v1; could become a deployment-time config later.
_DEFAULT_MIN_REFERENCES = 10


def check_reference_count(
    refs: list[Reference], *, minimum: int = _DEFAULT_MIN_REFERENCES
) -> list[Issue]:
    if len(refs) >= minimum:
        return []
    return [
        _GLOBAL_BUILDER.warning(
            code="reference_count_below_minimum",
            message=(
                f"Your reference list contains {len(refs)} sources; the assignment "
                f"rubric typically requires at least {minimum}."
            ),
            position=Position(start=0, end=0),
            suggestion=f"Add more sources to reach at least {minimum} references.",
        )
    ]


# ---------------------------------------------------------------------------
# Deprecated-phrase detection
# ---------------------------------------------------------------------------

# Phrases from non-APA-7 styles that often leak into student references.
_DEPRECATED_PHRASES = [
    # (regex, code, message, suggestion)
    (
        re.compile(r"\bRetrieved\s+from\b", re.IGNORECASE),
        "deprecated_retrieved_from",
        "'Retrieved from' is APA 6 style — APA 7 omits this phrase when a URL is present.",
        "Remove 'Retrieved from'; place the URL directly after the publisher/date.",
    ),
    (
        re.compile(r"\baccessed\b\s*[:\-]", re.IGNORECASE),
        "deprecated_accessed_date",
        "'Accessed: <date>' is a Chicago/Harvard convention — APA 7 omits access dates for stable web pages.",
        "Remove 'Accessed:' dates unless the page is unarchived and likely to change.",
    ),
    (
        re.compile(r"\bn\.p\.\b", re.IGNORECASE),
        "deprecated_no_publisher_marker",
        "'n.p.' is from older bibliographic style — APA 7 simply omits the publisher field when unknown.",
        "Delete the 'n.p.' marker.",
    ),
    (
        re.compile(r"\bibid\b\.?", re.IGNORECASE),
        "deprecated_ibid",
        "'Ibid.' is a Chicago / footnote convention — APA 7 uses author-year citations only.",
        "Replace 'Ibid.' with the full (Author, Year) citation.",
    ),
]


def check_deprecated_phrases(ref: Reference) -> list[Issue]:
    issues: list[Issue] = []
    for pattern, code, message, suggestion in _DEPRECATED_PHRASES:
        if pattern.search(ref.raw):
            issues.append(
                _REF_BUILDER.warning(
                    code=code,
                    message=message,
                    position=ref.position,
                    suggestion=suggestion,
                )
            )
    return issues
