"""
Simulation utilities for specification-backed mock providers.

These utilities allow mock providers to simulate realistic enterprise
behaviour: configurable latency, failure injection, and pagination.

Default configuration (safe for development and CI):
  - Zero latency simulation (instant responses)
  - No failure injection
  - Deterministic outputs

Failure modes map to real enterprise error scenarios so that callers
(supervisor, orchestration, tests) handle errors they will see in production.

NOTE — Specification alignment (ADR-004):
  Failure modes here simulate real ClaimCenter, PolicyCenter, and Azure
  API error responses. When real adapters are built, the same error types
  must be raised from the same conditions so that upstream error handling
  built against these mocks continues to work without changes.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar

from backend.app.integration.contracts.common import (
    PaginationRequest,
    PaginationResponse,
)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


class FailureMode(str, Enum):
    """
    Enterprise failure modes that mock providers can simulate.

    Each mode maps to a real error scenario in production enterprise systems.
    """

    NOT_FOUND = "not_found"          # 404 — resource does not exist or is not in portfolio
    UNAUTHORIZED = "unauthorized"    # 401 — missing or invalid authentication token
    FORBIDDEN = "forbidden"          # 403 — authenticated but insufficient permissions
    RATE_LIMITED = "rate_limited"    # 429 — API rate limit exceeded
    TIMEOUT = "timeout"              # 408/504 — upstream system did not respond in time
    UNAVAILABLE = "unavailable"      # 503 — upstream system is down or in maintenance
    PARTIAL_FAILURE = "partial"      # Partial data returned; some records missing


# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------


@dataclass
class SimulationConfig:
    """
    Per-request or per-provider simulation configuration.

    Attributes:
        latency_ms: Simulated response latency in milliseconds (default 0).
        failure_mode: If set, the mock will raise the corresponding error
            instead of returning data.
        fail_after_n: If set with a failure_mode, fail only after the first
            N successful calls (useful for testing retry logic).
    """

    latency_ms: int = 0
    failure_mode: FailureMode | None = None
    fail_after_n: int | None = None

    # Internal call counter (not part of configuration surface)
    _call_count: int = field(default=0, init=False, repr=False)

    def should_fail(self) -> bool:
        """Return True if the current call should simulate a failure."""
        if self.failure_mode is None:
            return False
        self._call_count += 1
        if self.fail_after_n is not None:
            return self._call_count > self.fail_after_n
        return True


# Default configuration — zero latency, no failures, safe for all envs
DEFAULT_SIM = SimulationConfig()


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------


def apply_simulation(config: SimulationConfig = DEFAULT_SIM) -> None:
    """
    Apply the simulation configuration for the current call.

    If latency is configured, sleeps for the specified duration.
    If a failure mode is configured and should trigger, imports and raises
    the appropriate mock error.

    Call this at the top of every mock provider method:

        def get_claim(self, claim_id, context):
            apply_simulation(self._sim)
            ...
    """
    if config.latency_ms > 0:
        time.sleep(config.latency_ms / 1000.0)

    if config.should_fail():
        _raise_for_mode(config.failure_mode)


def _raise_for_mode(mode: FailureMode) -> None:
    """Import and raise the appropriate mock error for a failure mode."""
    from backend.app.integration.mocks.errors import (
        MockForbiddenError,
        MockNotFoundError,
        MockRateLimitError,
        MockTimeoutError,
        MockUnauthorizedError,
        MockUnavailableError,
    )

    messages = {
        FailureMode.NOT_FOUND: "Resource not found (simulated).",
        FailureMode.UNAUTHORIZED: "Authentication token missing or invalid (simulated).",
        FailureMode.FORBIDDEN: "Insufficient permissions for this resource (simulated).",
        FailureMode.RATE_LIMITED: "API rate limit exceeded — retry after 60 seconds (simulated).",
        FailureMode.TIMEOUT: "Upstream system did not respond within the timeout window (simulated).",
        FailureMode.UNAVAILABLE: "Upstream system is unavailable — maintenance window or outage (simulated).",
        FailureMode.PARTIAL_FAILURE: "Partial data returned — some records are temporarily unavailable (simulated).",
    }

    error_map = {
        FailureMode.NOT_FOUND: MockNotFoundError,
        FailureMode.UNAUTHORIZED: MockUnauthorizedError,
        FailureMode.FORBIDDEN: MockForbiddenError,
        FailureMode.RATE_LIMITED: MockRateLimitError,
        FailureMode.TIMEOUT: MockTimeoutError,
        FailureMode.UNAVAILABLE: MockUnavailableError,
        FailureMode.PARTIAL_FAILURE: MockUnavailableError,
    }

    cls = error_map.get(mode, MockUnavailableError)
    raise cls(messages.get(mode, "Simulated failure."))


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------


def paginate(
    items: list[T],
    pagination: PaginationRequest | None,
) -> tuple[list[T], PaginationResponse]:
    """
    Apply pagination to a list of items.

    Returns (page_items, pagination_response).

    Usage:
        page_items, page_meta = paginate(all_claims, pagination)
        return GetClaimsResult(status=SUCCESS, claims=page_items, pagination=page_meta)
    """
    req = pagination or PaginationRequest()
    total = len(items)
    total_pages = max(1, math.ceil(total / req.page_size))
    page = max(1, min(req.page, total_pages))

    start = (page - 1) * req.page_size
    end = start + req.page_size
    page_items = items[start:end]

    meta = PaginationResponse(
        page=page,
        page_size=req.page_size,
        total_records=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    return page_items, meta
