from __future__ import annotations

import httpx

from .base import LookupResult


class HttpxUrlCheckClient:
    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s

    async def check(self, url: str) -> LookupResult:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_s,
                follow_redirects=True,
            ) as c:
                resp = await c.head(url)
                if resp.status_code == 405:
                    # Some servers reject HEAD; retry with GET.
                    resp = await c.get(url)
        except httpx.HTTPError as exc:
            return LookupResult.unavailable(f"http_error: {type(exc).__name__}")
        if resp.status_code == 404 or resp.status_code == 410:
            return LookupResult.not_found()
        if resp.status_code >= 500:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        if resp.status_code >= 400:
            return LookupResult.unavailable(f"http_{resp.status_code}")
        return LookupResult.found({"final_url": str(resp.url)})
