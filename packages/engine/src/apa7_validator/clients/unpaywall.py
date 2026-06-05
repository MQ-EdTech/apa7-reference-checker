from __future__ import annotations

from typing import Any

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
        data: dict[str, Any] = resp.json()
        return LookupResult.found(
            {
                "is_oa": bool(data.get("is_oa")),
                "oa_locations_count": len(data.get("oa_locations", [])),
            }
        )
