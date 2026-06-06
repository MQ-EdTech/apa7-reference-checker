"""Two-tier classification of references for the rubric source-quality check.

Tier 1 — Peer-reviewed / books.
Tier 3 — Everything else (no academic rigour, or publisher cannot be verified).

Tier 2 (accountable publisher without peer review — gov, news, established
NGOs, corporate self-publication) is intentionally not implemented in v1;
deferred to a follow-up so we can decide on classification rules carefully.
For v1 every non-Tier-1 reference falls into Tier 3.
"""

from __future__ import annotations

from .models import Reference, ReferenceType

_TIER_1_TYPES = frozenset(
    {ReferenceType.JOURNAL_ARTICLE, ReferenceType.BOOK, ReferenceType.BOOK_CHAPTER}
)


def classify_tier(ref: Reference) -> int:
    """Return 1 or 3."""
    if ref.ref_type in _TIER_1_TYPES:
        return 1
    return 3
