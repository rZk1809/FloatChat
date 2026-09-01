"""In-memory per-session query history store."""

import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class HistoryEntry:
    query: str
    main_response: str
    timestamp: float
    elapsed_ms: int


_sessions: dict[str, list[HistoryEntry]] = defaultdict(list)
_MAX_ENTRIES = 50
_SESSION_TTL_S = 7200


def record_query(session_id: str, query: str, response: str, elapsed_ms: int) -> None:
    entries = _sessions[session_id]
    entries.append(HistoryEntry(query=query, main_response=response, timestamp=time.time(), elapsed_ms=elapsed_ms))
    if len(entries) > _MAX_ENTRIES:
        del entries[0]


def get_history(session_id: str) -> list[dict[str, Any]]:
    return [asdict(e) for e in _sessions.get(session_id, [])]


def clear_history(session_id: str) -> int:
    count = len(_sessions.get(session_id, []))
    _sessions.pop(session_id, None)
    return count


def evict_stale_sessions() -> int:
    now = time.time()
    stale = [sid for sid, entries in _sessions.items() if entries and now - entries[-1].timestamp > _SESSION_TTL_S]
    for sid in stale:
        del _sessions[sid]
    return len(stale)
