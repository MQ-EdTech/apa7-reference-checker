# packages/engine/src/apa7_validator/validators/cross_matching.py
from __future__ import annotations

from collections import defaultdict

from ..models import Citation, Issue, Reference
from .base import IssueBuilder

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
            issues.append(
                _CIT_B.error(
                    code="citation_without_reference",
                    message=f"In-text citation '{cit.raw}' has no matching reference list entry",
                    position=cit.position,
                    suggestion="Add a reference list entry, or correct the author/year in the citation",
                )
            )
        elif len(candidates) > 1:
            issues.append(
                _CIT_B.warning(
                    code="ambiguous_match",
                    message=(
                        f"Citation '{cit.raw}' matches multiple reference list entries; "
                        f"disambiguate by adding letter suffixes (e.g., 2020a, 2020b)"
                    ),
                    position=cit.position,
                    suggestion="Append 'a', 'b', ... to the year of same-author-same-year references",
                )
            )
            for ref in candidates:
                matched_refs.add(id(ref))
        else:
            matched_refs.add(id(candidates[0]))

    for ref in refs:
        if id(ref) not in matched_refs:
            issues.append(
                _REF_B.warning(
                    code="reference_uncited",
                    message=(
                        f"Reference '{ref.authors[0].family if ref.authors else '?'}, {ref.year}' "
                        "is not cited in the body"
                    ),
                    position=ref.position,
                    suggestion="Cite the reference in the body, or remove it from the reference list",
                )
            )

    return issues
