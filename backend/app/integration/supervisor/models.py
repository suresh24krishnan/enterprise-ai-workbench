"""
Supervisor data models — input, output, and execution trace types.

All types are Pydantic models so they can be serialised by FastAPI
without any extra configuration.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SupervisorStatus(str, Enum):
    """Outcome of a supervisor execution run."""

    SUCCESS = "success"
    PARTIAL = "partial"     # Some providers succeeded, others failed
    FAILED = "failed"       # All providers failed or governance blocked


class ClaimIntent(str, Enum):
    """
    Supported claim-processing intents.

    Each intent maps to a fixed set of providers. The mapping is defined
    in planner.py and does not change at runtime.
    """

    CLAIM_SUMMARY = "claim_summary"
    COVERAGE_ANALYSIS = "coverage_analysis"
    FRAUD_CHECK = "fraud_check"
    DOCUMENT_REVIEW = "document_review"
    POLICY_LOOKUP = "policy_lookup"


class ProviderTrace(BaseModel):
    """Execution trace entry for a single provider call."""

    provider: str
    method: str
    status: str                          # success | not_found | error | skipped
    latency_ms: float
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool = False


class GovernanceFlags(BaseModel):
    """Governance state captured at execution time."""

    writes_enabled: bool = False
    provider_mode_enforced: str = "mock"
    real_providers_rejected: bool = True
    all_operations_read_only: bool = True
    phase_2b_gate_open: bool = False


class SupervisorRequest(BaseModel):
    """Input to the supervisor endpoint."""

    claim_id: str = Field(description="Claim to fetch intelligence for")
    intent: str = Field(
        default="claim_summary",
        description="Processing intent — see ClaimIntent enum for values",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional caller-supplied context (not used to change governance)",
    )


class SupervisorResponse(BaseModel):
    """Unified output from the supervisor for a single intent execution."""

    request_id: str
    intent: str
    selected_providers: list[str]
    execution_trace: list[ProviderTrace]
    aggregated_result: dict[str, Any]
    status: SupervisorStatus
    governance_flags: GovernanceFlags
    latency_ms: float
    provider_count: int
    succeeded_count: int
    failed_count: int
