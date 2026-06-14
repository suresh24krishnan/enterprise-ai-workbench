"""
PolicyCenter enterprise provider contracts.

Defines the read interface that all PolicyCenter provider implementations
must satisfy — mock, hybrid, and real.

IMPORTANT — Specification alignment (ADR-004):
  These contracts represent the platform's required interface. When the real
  adapter is implemented in Sprint 2+, all field names and structures must
  be derived from the published Guidewire PolicyCenter REST API specification.

  Key mapping notes:
    - PolicyCenter uses 'policyNumber' as the human-readable identifier.
      The platform uses 'policy_id' as the stable technical key.
    - Coverage structures in PolicyCenter are deeply nested under
      PolicyPeriod → PolicyLine → Coverage. The adapter must flatten
      to these CoverageSummary models.
    - Policy limits and deductibles are stored as CovTerms in PolicyCenter.
      The adapter must extract and normalise them to LimitSummary and
      DeductibleSummary.

No write interface is defined for PolicyCenter in Phase 2. Policy
modifications are out of scope for the claims processing platform.

ERROR HANDLING (all implementations):
  - 404: policy not associated with this adjuster's claim portfolio → NOT_FOUND
  - 403: adjuster lacks read permission → PERMISSION_DENIED
  - 429: rate limit exceeded → RATE_LIMITED (retryable=True)
  - 503: PolicyCenter unavailable → UNAVAILABLE (retryable=True)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from backend.app.integration.contracts.common import (
    ClaimLineOfBusiness,
    MoneyAmount,
    PaginationRequest,
    PaginationResponse,
    PartySummary,
    ProviderStatus,
    SourceSystem,
    ToolError,
    ToolExecutionContext,
    ToolResultStatus,
)


# ---------------------------------------------------------------------------
# PolicyCenter-specific enums
# ---------------------------------------------------------------------------


class PolicyStatus(str, Enum):
    """Normalised policy status vocabulary."""

    IN_FORCE = "in_force"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RESCINDED = "rescinded"
    PENDING = "pending"


class CoverageStatus(str, Enum):
    """Status of an individual coverage on a policy."""

    ACTIVE = "active"
    EXCLUDED = "excluded"
    WAIVED = "waived"
    CANCELLED = "cancelled"


class LimitType(str, Enum):
    """Type of policy limit."""

    PER_OCCURRENCE = "per_occurrence"
    AGGREGATE = "aggregate"
    PER_PERSON = "per_person"
    PER_ACCIDENT = "per_accident"
    SPLIT = "split"


class DeductibleType(str, Enum):
    """Type of policy deductible."""

    FLAT = "flat"
    PERCENTAGE = "percentage"
    DISAPPEARING = "disappearing"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PolicySummary(BaseModel):
    """
    Lightweight policy record for claim association and coverage lookup.

    NOTE: 'policy_id' is the platform identifier. Map from PolicyCenter's
    'policyNumber' and internal policy entity ID at the adapter boundary.
    """

    policy_id: str
    policy_number: str = Field(description="Human-readable policy number")
    line_of_business: ClaimLineOfBusiness
    status: PolicyStatus
    effective_date: date
    expiration_date: date
    insured: PartySummary | None = None
    carrier: str | None = None
    program: str | None = None
    source_system: SourceSystem = SourceSystem.POLICYCENTER


class CoverageSummary(BaseModel):
    """
    An individual coverage on a policy, relevant to a specific claim line.

    NOTE — Specification alignment:
      PolicyCenter Coverage entities are nested under PolicyLine. The
      adapter must traverse PolicyPeriod → PolicyLine → Coverage and
      map the CovTerms to the limit and deductible fields here.
    """

    coverage_id: str
    policy_id: str
    coverage_type: str = Field(
        description="Coverage type code, e.g. 'BI', 'PD', 'COMP', 'COLL'"
    )
    coverage_description: str | None = None
    status: CoverageStatus
    effective_date: date | None = None
    expiration_date: date | None = None
    per_occurrence_limit: MoneyAmount | None = None
    aggregate_limit: MoneyAmount | None = None
    deductible: MoneyAmount | None = None
    applies_to_claim_line: str | None = Field(
        default=None,
        description="Claim line or exposure type this coverage applies to",
    )


class LimitSummary(BaseModel):
    """
    A single policy limit extracted from a PolicyCenter CovTerm.

    NOTE — Specification alignment:
      PolicyCenter stores limits as CovTerms with a 'PatternCode' identifying
      the limit type. Map CovTerms with numeric values to this model.
    """

    limit_id: str
    coverage_id: str
    policy_id: str
    limit_type: LimitType
    amount: MoneyAmount
    description: str | None = None


class DeductibleSummary(BaseModel):
    """
    A single policy deductible extracted from a PolicyCenter CovTerm.
    """

    deductible_id: str
    coverage_id: str
    policy_id: str
    deductible_type: DeductibleType
    amount: MoneyAmount | None = None
    percentage: Decimal | None = Field(
        default=None,
        description="For percentage deductibles, the percentage (0.0–100.0)",
    )
    description: str | None = None


class EndorsementSummary(BaseModel):
    """
    A policy endorsement or rider that modifies base coverage terms.
    """

    endorsement_id: str
    policy_id: str
    endorsement_number: str | None = None
    description: str
    effective_date: date | None = None
    expiration_date: date | None = None
    premium_impact: MoneyAmount | None = None


# ---------------------------------------------------------------------------
# Provider result wrappers
# ---------------------------------------------------------------------------


class GetPolicyResult(BaseModel):
    status: ToolResultStatus
    policy: PolicySummary | None = None
    error: ToolError | None = None


class GetPolicyCoveragesResult(BaseModel):
    status: ToolResultStatus
    coverages: list[CoverageSummary] = Field(default_factory=list)
    error: ToolError | None = None


class GetPolicyLimitsResult(BaseModel):
    status: ToolResultStatus
    limits: list[LimitSummary] = Field(default_factory=list)
    error: ToolError | None = None


class GetPolicyDeductiblesResult(BaseModel):
    status: ToolResultStatus
    deductibles: list[DeductibleSummary] = Field(default_factory=list)
    error: ToolError | None = None


class GetEndorsementsResult(BaseModel):
    status: ToolResultStatus
    endorsements: list[EndorsementSummary] = Field(default_factory=list)
    error: ToolError | None = None


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class IPolicyCenterReadProvider(Protocol):
    """
    Read interface for PolicyCenter.

    All implementations — mock, hybrid, real — must satisfy this protocol.

    SPECIFICATION ALIGNMENT (ADR-004):
      The real adapter must be derived from Guidewire PolicyCenter REST API
      documentation. Do not implement the real adapter until the specification
      is received and field mappings are documented in the adapter header.
    """

    def health(self) -> ProviderStatus:
        """Report provider operational status."""
        ...

    def get_policy(
        self,
        policy_id: str,
        context: ToolExecutionContext,
    ) -> GetPolicyResult:
        """Retrieve a policy by platform policy ID."""
        ...

    def get_policy_coverages(
        self,
        policy_id: str,
        context: ToolExecutionContext,
        line_of_business: ClaimLineOfBusiness | None = None,
    ) -> GetPolicyCoveragesResult:
        """Retrieve all active coverages for a policy, optionally filtered by LOB."""
        ...

    def get_policy_limits(
        self,
        policy_id: str,
        coverage_id: str | None,
        context: ToolExecutionContext,
    ) -> GetPolicyLimitsResult:
        """Retrieve policy limits, optionally scoped to a specific coverage."""
        ...

    def get_policy_deductibles(
        self,
        policy_id: str,
        coverage_id: str | None,
        context: ToolExecutionContext,
    ) -> GetPolicyDeductiblesResult:
        """Retrieve deductibles for a policy, optionally scoped to a coverage."""
        ...

    def get_endorsements(
        self,
        policy_id: str,
        context: ToolExecutionContext,
    ) -> GetEndorsementsResult:
        """Retrieve all endorsements on a policy."""
        ...
