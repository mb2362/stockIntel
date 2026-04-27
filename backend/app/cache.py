"""Redis caching layer for StockIntel backend.

Provides a unified cache interface with:
- Automatic JSON serialization/deserialization
- Configurable TTL per cache entry
- Graceful degradation when Redis is unavailable (in-memory fallback)
- Cache key namespacing to avoid collisions
"""
from __future__ import annotations

import json
import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ── Redis client (optional) ────────────────────────────────────────────────────

_redis_client = None


def _get_redis():
    """Return a Redis client, or None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        _redis_client = client
        logger.info("Redis connected at %s", url)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable (%s) – using in-memory fallback", exc)
        return None


# ── In-memory fallback ─────────────────────────────────────────────────────────

class _InMemoryStore:
    """Simple TTL-aware dict used when Redis is not available."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        expires_at = (time.time() + ex) if ex else 0.0
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def flushdb(self) -> None:
        self._store.clear()

    def keys(self, pattern: str = "*") -> list[str]:
        import fnmatch
        now = time.time()
        live = {k for k, (_, exp) in self._store.items() if not exp or now <= exp}
        return [k for k in live if fnmatch.fnmatch(k, pattern)]


_fallback_store = _InMemoryStore()


# ── Public API ─────────────────────────────────────────────────────────────────

# Cache TTLs (seconds)
TTL_QUOTE = int(os.getenv("CACHE_TTL_QUOTE", "15"))       # live prices
TTL_HISTORICAL = int(os.getenv("CACHE_TTL_HISTORICAL", "300"))  # 5 min – OHLCV bars
TTL_INFO = int(os.getenv("CACHE_TTL_INFO", "3600"))        # 1 hour – company info
TTL_OVERVIEW = int(os.getenv("CACHE_TTL_OVERVIEW", "60"))  # market overview
TTL_NEWS = int(os.getenv("CACHE_TTL_NEWS", "600"))         # 10 min – news articles
TTL_PREDICT = int(os.getenv("CACHE_TTL_PREDICT", "300"))   # predictions


def _store():
    """Return Redis client or in-memory fallback."""
    return _get_redis() or _fallback_store


def cache_get(key: str) -> Optional[Any]:
    """Retrieve and deserialize a cached value. Returns None on miss."""
    try:
        raw = _store().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.debug("cache_get error for key %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int = TTL_QUOTE) -> bool:
    """Serialize and store a value with TTL (seconds). Returns True on success."""
    try:
        _store().set(key, json.dumps(value, default=str), ex=ttl)
        return True
    except Exception as exc:
        logger.debug("cache_set error for key %s: %s", key, exc)
        return False


def cache_delete(key: str) -> None:
    """Remove a single key from the cache."""
    try:
        _store().delete(key)
    except Exception as exc:
        logger.debug("cache_delete error for key %s: %s", key, exc)


def cache_flush() -> None:
    """Clear the entire cache (use with care)."""
    try:
        _store().flushdb()
    except Exception as exc:
        logger.debug("cache_flush error: %s", exc)


def make_key(*parts: str) -> str:
    """Build a namespaced cache key.

    Example: make_key("quote", "AAPL") -> "stockintel:quote:AAPL"
    """
    return "stockintel:" + ":".join(str(p) for p in parts)


# ── Decorator ─────────────────────────────────────────────────────────────────

def cached(ttl: int = TTL_QUOTE, key_fn: Optional[Callable[..., str]] = None):
    """Decorator that caches the return value of a sync function.

    Args:
        ttl: Cache TTL in seconds.
        key_fn: Optional callable to derive the cache key from the function
                arguments. Defaults to ``make_key(func.__name__, *args, **sorted_kwargs)``.

    Usage::

        @cached(ttl=TTL_QUOTE)
        def get_quote(symbol: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_fn is not None:
                key = key_fn(*args, **kwargs)
            else:
                kw_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                parts = [func.__name__] + [str(a) for a in args]
                if kw_str:
                    parts.append(kw_str)
                key = make_key(*parts)

            cached_value = cache_get(key)
            if cached_value is not None:
                logger.debug("cache HIT: %s", key)
                return cached_value

            logger.debug("cache MISS: %s", key)
            result = func(*args, **kwargs)
            cache_set(key, result, ttl=ttl)
            return result

        wrapper._cache_ttl = ttl  # expose for introspection in tests
        return wrapper

    return decorator


def invalidate_quote(symbol: str) -> None:
    """Invalidate all cached data for a specific stock symbol."""
    for suffix in ("quote", "historical", "info", "indicators", "news"):
        cache_delete(make_key(suffix, symbol.upper()))
