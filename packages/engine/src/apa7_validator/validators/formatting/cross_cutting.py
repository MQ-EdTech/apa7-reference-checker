from __future__ import annotations

import re

from ...models import Issue, Reference
from ..base import IssueBuilder

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
