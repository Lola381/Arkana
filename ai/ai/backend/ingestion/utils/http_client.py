"""
Arkana — Async HTTP Client with Rate Limiting & Retry Logic
Shared utility for all extractors. Implements:
  - Token bucket rate limiter (per-source)
  - Exponential backoff with jitter
  - Descriptive User-Agent injection
  - Request logging
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import aiohttp

from ingestion.config import (
    MAX_CONCURRENT,
    MAX_RETRIES,
    RATE_LIMITS,
    RETRY_BASE_DELAY,
    RETRY_JITTER,
    RETRY_MAX_DELAY,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


# ── Token Bucket Rate Limiter ─────────────────────────────────────────────────

class TokenBucket:
    """
    Simple async token bucket for per-source rate limiting.
    rate: tokens per second (= max requests per second)
    """

    def __init__(self, rate: float) -> None:
        self.rate = rate
        self.tokens = rate
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            # Refill tokens
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# ── Global Rate Limiters & Semaphores ────────────────────────────────────────

_buckets: dict[str, TokenBucket] = {}
_semaphores: dict[str, asyncio.Semaphore] = {}


def _get_bucket(source: str) -> TokenBucket:
    if source not in _buckets:
        rate = RATE_LIMITS.get(source, 1.0)
        _buckets[source] = TokenBucket(rate)
    return _buckets[source]


def _get_semaphore(source: str) -> asyncio.Semaphore:
    if source not in _semaphores:
        max_conn = MAX_CONCURRENT.get(source, 2)
        _semaphores[source] = asyncio.Semaphore(max_conn)
    return _semaphores[source]


# ── Retry Logic ───────────────────────────────────────────────────────────────

def _compute_backoff(attempt: int) -> float:
    """Exponential backoff with optional jitter."""
    delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
    if RETRY_JITTER:
        delay = delay * (0.5 + random.random() * 0.5)
    return delay


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ── Main HTTP Client ──────────────────────────────────────────────────────────

class ArkanaHTTPClient:
    """
    Async HTTP client with rate limiting and retry logic.
    Use as a context manager or create a shared instance per extractor.

    Usage:
        async with ArkanaHTTPClient("wikipedia") as client:
            data = await client.get_json("https://en.wikipedia.org/...")
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.bucket = _get_bucket(source)
        self.semaphore = _get_semaphore(source)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "ArkanaHTTPClient":
        self._session = aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session:
            await self._session.close()

    async def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """GET request → parsed JSON. Raises on non-200 after all retries."""
        return await self._request("GET", url, params=params, headers=headers)

    async def post_json(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """POST request → parsed JSON."""
        return await self._request("POST", url, data=data, json=json, headers=headers)

    async def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        """GET request → raw text."""
        return await self._request("GET", url, params=params, as_text=True)

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        as_text: bool = False,
    ) -> Any:
        if self._session is None:
            raise RuntimeError("Client not started. Use as async context manager.")

        for attempt in range(MAX_RETRIES + 1):
            await self.bucket.acquire()
            async with self.semaphore:
                try:
                    async with self._session.request(
                        method,
                        url,
                        params=params,
                        data=data,
                        json=json,
                        headers=headers,
                    ) as resp:
                        if resp.status == 200:
                            if as_text:
                                return await resp.text()
                            return await resp.json(content_type=None)

                        if resp.status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                            delay = _compute_backoff(attempt)
                            logger.warning(
                                f"[{self.source}] HTTP {resp.status} for {url} "
                                f"— retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                            )
                            await asyncio.sleep(delay)
                            continue

                        resp.raise_for_status()

                except aiohttp.ClientConnectorError as e:
                    if attempt < MAX_RETRIES:
                        delay = _compute_backoff(attempt)
                        logger.warning(
                            f"[{self.source}] Connection error: {e} "
                            f"— retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise

                except asyncio.TimeoutError:
                    if attempt < MAX_RETRIES:
                        delay = _compute_backoff(attempt)
                        logger.warning(
                            f"[{self.source}] Timeout for {url} "
                            f"— retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise

        raise RuntimeError(f"[{self.source}] All {MAX_RETRIES} retries exhausted for {url}")
