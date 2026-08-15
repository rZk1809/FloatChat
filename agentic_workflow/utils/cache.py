"""
Simple TTL (time-to-live) in-memory cache for tool results.
Avoids redundant ChromaDB / PostgreSQL calls for identical queries
within the same session.
"""

import time
import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 300  # seconds


class TTLCache:
    """Thread-unsafe single-process TTL cache; suitable for single-user CLI/Streamlit sessions."""

    def __init__(self, ttl: int = _DEFAULT_TTL, max_size: int = 128) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}

    @staticmethod
    def _key(*args: Any, **kwargs: Any) -> str:
        raw = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        key = self._key(*args, **kwargs)
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, value: Any, *args: Any, **kwargs: Any) -> None:
        if len(self._store) >= self._max_size:
            self._evict_oldest()
        key = self._key(*args, **kwargs)
        self._store[key] = (value, time.monotonic() + self._ttl)

    def _evict_oldest(self) -> None:
        now = time.monotonic()
        # First remove expired entries
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        # If still over limit, remove the entry with the earliest expiry
        if len(self._store) >= self._max_size:
            oldest = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest]

    def invalidate(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


# Module-level caches shared across tool calls in a session
retriever_cache = TTLCache(ttl=300)
sql_cache = TTLCache(ttl=60)
analyzer_cache = TTLCache(ttl=120)
