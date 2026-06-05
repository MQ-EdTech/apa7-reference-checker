from __future__ import annotations

from typing import Any

import httpx

from .base import LookupResult


class HttpxOpenLibraryClient:
    """Look up ISBNs against openlibrary.org."""

    BASE = "https://openlibrary.org/isbn/"

    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s

    async def lookup_isbn(self, isbn: str) -> LookupResult:
        url = f"{self.BASE}{isbn}.json"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s, follow_redirects=True) as c:
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
        return LookupResult.found({"title": data.get("title", "")})
