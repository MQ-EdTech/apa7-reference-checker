from __future__ import annotations

from typing import Any

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
        payload: dict[str, Any] = resp.json()
        data: dict[str, Any] = payload.get("message", {})
        issued_raw: dict[str, Any] = data.get("issued") or {}
        date_parts: list[list[Any]] = issued_raw.get("date-parts", [[None]])
        return LookupResult.found(
            {
                "title": (data.get("title") or [""])[0],
                "type": data.get("type", ""),
                "issued": date_parts[0][0],
            }
        )
