"""
In-memory trace store for Control Tower runs.

LAB ONLY — not for production use.

Design:
  - Fixed-capacity ring buffer (25 entries, oldest evicted on overflow).
  - No disk persistence. Cleared on process restart.
  - Thread-safe via a simple lock (single-worker Uvicorn is fine without one,
    but the lock makes the intent explicit).
  - No secrets, no document content, no email bodies stored.

Production evolution:
  Replace this module with a persistent store (PostgreSQL, OpenTelemetry
  exporter, or SIEM sink) without changing the Control Tower API surface.
  The service.py and API layers remain unchanged.
"""

from __future__ import annotations

import threading
from collections import deque

from .models import ControlTowerRun

_MAX_RUNS = 25
_store: deque[ControlTowerRun] = deque(maxlen=_MAX_RUNS)
_lock = threading.Lock()


def record_run(run: ControlTowerRun) -> None:
    """Append a run to the store. Oldest entry is evicted when full."""
    with _lock:
        _store.append(run)


def get_runs(limit: int = 25) -> list[ControlTowerRun]:
    """Return up to `limit` most-recent runs, newest first."""
    with _lock:
        runs = list(_store)
    runs.reverse()
    return runs[:limit]


def get_run(request_id: str) -> ControlTowerRun | None:
    """Return a single run by request_id, or None if not found."""
    with _lock:
        for run in _store:
            if run.request_id == request_id:
                return run
    return None


def store_size() -> int:
    """Return the current number of stored runs."""
    with _lock:
        return len(_store)


def store_capacity() -> int:
    return _MAX_RUNS
