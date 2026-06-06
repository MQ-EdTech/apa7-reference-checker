"""Detect references whose URL is an institutional library proxy / gateway.

A reference whose URL points to ebookcentral.proquest.com/lib/<inst>/... or
similar library-proxy gateway is not citing the canonical source — the URL is
session-bound, authentication-gated, and unstable. The student should locate
the source's canonical DOI / ISBN and cite that instead.
"""

from __future__ import annotations

import re

from ..models import Issue, Reference
from .base import IssueBuilder

_B = IssueBuilder(target_kind="reference")

# Library-proxy URL patterns. Conservative — match clear gateway URLs only.
# Canvas / Moodle / Blackboard / Echo360 / LinkedIn Learning etc. are LMS or
# learning-platform URLs and are NOT flagged here (per user instruction —
# strict-mode toggle for those will come in a future version).
_LIBRARY_PROXY_PATTERNS = [
    re.compile(r"ebookcentral\.proquest\.com", re.IGNORECASE),
    re.compile(
        r"web\.b\.ebscohost\.com|eds\.b\.ebscohost\.com|search\.ebscohost\.com", re.IGNORECASE
    ),
    re.compile(r"\.libproxy\.", re.IGNORECASE),
    re.compile(r"\.lib\.[\w\-]+\.edu", re.IGNORECASE),
    re.compile(r"go\.gale\.com/ps/i\.do\?", re.IGNORECASE),
    re.compile(r"link\.gale\.com/apps/doc/", re.IGNORECASE),
    re.compile(r"\.libguides\.com", re.IGNORECASE),
]


def _is_library_proxy(url: str | None) -> bool:
    if not url:
        return False
    return any(p.search(url) for p in _LIBRARY_PROXY_PATTERNS)


def check_library_proxy_url(ref: Reference) -> list[Issue]:
    # Check both the explicit url field and the raw text — many library-proxy
    # URLs are stored in raw text even when the parser didn't extract them.
    url_candidates = [ref.url] if ref.url else []
    # Search raw text for any http URL that matches a proxy pattern.
    if ref.raw:
        for match in re.finditer(r"https?://\S+", ref.raw):
            url_candidates.append(match.group(0))

    for url in url_candidates:
        if _is_library_proxy(url):
            return [
                _B.error(
                    code="reference_uses_library_proxy_url",
                    message=(
                        "Reference uses an institutional library proxy URL "
                        "instead of the canonical source. Library-proxy links "
                        "are session-bound and only work for users authenticated "
                        "through that institution."
                    ),
                    position=ref.position,
                    suggestion=(
                        "Locate the source's canonical DOI / ISBN / publisher URL "
                        "and cite that instead of the proxy URL."
                    ),
                )
            ]
    return []
