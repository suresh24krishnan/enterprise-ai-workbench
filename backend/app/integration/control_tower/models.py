"""
Control Tower data models — serialisable, secret-free, body-free.

These models are the Control Tower's public surface. They contain only
metadata that is safe to expose in an operational dashboard:
  - timing (latency per provider, total)
  - status outcomes
  - governance decisions
  - provider mode
  - aggregate counts

What is intentionally EXCLUDED:
  - claim document content (UNTRUSTED DATA — ADR-006)
  - email body text (UNTRUSTED DATA — ADR-006)
  - API tokens, credentials, secrets
  - internal stack traces
  - raw provider response bodies
"""

from __future__ import annotations

from pydantic import BaseModel


class ControlTowerProviderStep(BaseModel):
    """Per-provider execution trace entry — timing and outcome only."""

    provider: str
    method: str
    status: str           # success | not_found | error
    latency_ms: float
    retryable: bool = False
    error_code: str | None = None
    # error_message is included when present — it contains no secrets or body text
    error_message: str | None = None


class ControlTowerGovernanceSummary(BaseModel):
    """Governance decision captured at execution time."""

    writes_enabled: bool
    provider_mode_enforced: str
    real_providers_rejected: bool
    all_operations_read_only: bool
    phase_2b_gate_open: bool


class ControlTowerRun(BaseModel):
    """
    Full record of a single supervisor execution.

    Stored in the in-memory trace store. Serialised for the detail endpoint.
    """

    request_id: str
    claim_id: str
    intent: str
    selected_providers: list[str]
    steps: list[ControlTowerProviderStep]
    governance: ControlTowerGovernanceSummary
    status: str             # success | partial | failed
    latency_ms: float
    provider_count: int
    succeeded_count: int
    failed_count: int
    recorded_at: str        # ISO-8601 UTC timestamp


class ControlTowerRunSummary(BaseModel):
    """Lightweight summary for the runs list endpoint."""

    request_id: str
    claim_id: str
    intent: str
    status: str
    provider_count: int
    succeeded_count: int
    failed_count: int
    latency_ms: float
    writes_enabled: bool
    provider_mode: str
    recorded_at: str


class ControlTowerSummary(BaseModel):
    """Aggregate statistics across all stored runs."""

    total_runs: int
    success_count: int
    partial_count: int
    failed_count: int
    average_latency_ms: float
    writes_enabled: bool
    lab_safe: bool
    provider_modes: list[str]
    store_capacity: int
    store_used: int
