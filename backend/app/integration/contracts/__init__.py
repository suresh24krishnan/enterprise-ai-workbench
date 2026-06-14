"""
Enterprise provider contracts — Sprint 1.

All provider interfaces and data models are exported from this package.
Import from here rather than from individual contract modules to maintain
a stable public API surface as contracts evolve.

Usage:
    from backend.app.integration.contracts import (
        IClaimCenterReadProvider,
        ClaimDetail,
        ToolExecutionContext,
        ProviderMode,
    )
"""

# ---------------------------------------------------------------------------
# Common models and enums
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.common import (
    AddressSummary,
    ClaimLineOfBusiness,
    ClaimStatus,
    EvidenceReference,
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
# ClaimCenter contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.claimcenter import (
    # Enums
    ActivityType,
    ExposureStatus,
    NoteType,
    ReserveType,
    # Read models
    ActivitySummary,
    ClaimDetail,
    ClaimNote,
    ClaimSummary,
    ExposureSummary,
    PaymentSummary,
    ReserveSummary,
    # Write models (Phase 2B — disabled)
    CreateActivityRequest,
    CreateClaimNoteRequest,
    WriteOperationResult,
    # Result wrappers
    GetActivitiesResult,
    GetClaimNotesResult,
    GetClaimResult,
    GetClaimsResult,
    GetExposuresResult,
    GetPaymentsResult,
    GetReservesResult,
    # Provider protocols
    IClaimCenterReadProvider,
    IClaimCenterWriteProvider,
)

# ---------------------------------------------------------------------------
# PolicyCenter contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.policycenter import (
    # Enums
    CoverageStatus,
    DeductibleType,
    LimitType,
    PolicyStatus,
    # Models
    CoverageSummary,
    DeductibleSummary,
    EndorsementSummary,
    LimitSummary,
    PolicySummary,
    # Result wrappers
    GetEndorsementsResult,
    GetPolicyCoveragesResult,
    GetPolicyDeductiblesResult,
    GetPolicyLimitsResult,
    GetPolicyResult,
    # Provider protocol
    IPolicyCenterReadProvider,
)

# ---------------------------------------------------------------------------
# EDW contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.edw import (
    # Enums
    LossTrendDirection,
    RiskTier,
    # Models
    ClaimHistorySummary,
    CustomerProfile,
    LossTrendSummary,
    RiskProfile,
    # Result wrappers
    GetClaimHistoryResult,
    GetCustomerProfileResult,
    GetLossTrendsResult,
    GetRiskProfileResult,
    # Provider protocol
    IEDWReadProvider,
)

# ---------------------------------------------------------------------------
# Document contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.documents import (
    # Enums
    DocumentMimeType,
    DocumentStatus,
    DocumentType,
    # Models
    DocumentDetail,
    DocumentEvidence,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentSummary,
    # Result wrappers
    GetDocumentEvidenceResult,
    GetDocumentResult,
    GetDocumentsResult,
    GetDocumentTextResult,
    SearchDocumentsResult,
    # Provider protocol
    IDocumentReadProvider,
)

# ---------------------------------------------------------------------------
# Fraud contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.fraud import (
    # Enums
    FraudIndicatorType,
    FraudRiskLevel,
    SIURecommendationStatus,
    # Models
    FraudAssessment,
    FraudIndicator,
    SIURecommendation,
    # Result wrappers
    GetFraudIndicatorsResult,
    GetSIURecommendationResult,
    # Provider protocol
    IFraudReadProvider,
)

# ---------------------------------------------------------------------------
# Email contracts
# ---------------------------------------------------------------------------
from backend.app.integration.contracts.email import (
    # Enums
    DraftEmailPurpose,
    DraftEmailTone,
    EmailDirection,
    EmailStatus,
    # Models
    DraftEmailRequest,
    DraftEmailResult,
    EmailMessage,
    EmailSummary,
    EmailThread,
    # Result wrappers
    GetClaimCorrespondenceResult,
    GetEmailThreadResult,
    # Provider protocols
    IEmailDraftProvider,
    IEmailReadProvider,
)

# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

__all__ = [
    # Common
    "AddressSummary",
    "ClaimLineOfBusiness",
    "ClaimStatus",
    "EvidenceReference",
    "MoneyAmount",
    "PaginationRequest",
    "PaginationResponse",
    "PartySummary",
    "ProviderStatus",
    "SourceSystem",
    "ToolError",
    "ToolExecutionContext",
    "ToolResultStatus",
    # ClaimCenter — enums
    "ActivityType",
    "ExposureStatus",
    "NoteType",
    "ReserveType",
    # ClaimCenter — models
    "ActivitySummary",
    "ClaimDetail",
    "ClaimNote",
    "ClaimSummary",
    "ExposureSummary",
    "PaymentSummary",
    "ReserveSummary",
    "CreateActivityRequest",
    "CreateClaimNoteRequest",
    "WriteOperationResult",
    # ClaimCenter — results
    "GetActivitiesResult",
    "GetClaimNotesResult",
    "GetClaimResult",
    "GetClaimsResult",
    "GetExposuresResult",
    "GetPaymentsResult",
    "GetReservesResult",
    # ClaimCenter — protocols
    "IClaimCenterReadProvider",
    "IClaimCenterWriteProvider",
    # PolicyCenter — enums
    "CoverageStatus",
    "DeductibleType",
    "LimitType",
    "PolicyStatus",
    # PolicyCenter — models
    "CoverageSummary",
    "DeductibleSummary",
    "EndorsementSummary",
    "LimitSummary",
    "PolicySummary",
    # PolicyCenter — results
    "GetEndorsementsResult",
    "GetPolicyCoveragesResult",
    "GetPolicyDeductiblesResult",
    "GetPolicyLimitsResult",
    "GetPolicyResult",
    # PolicyCenter — protocol
    "IPolicyCenterReadProvider",
    # EDW — enums
    "LossTrendDirection",
    "RiskTier",
    # EDW — models
    "ClaimHistorySummary",
    "CustomerProfile",
    "LossTrendSummary",
    "RiskProfile",
    # EDW — results
    "GetClaimHistoryResult",
    "GetCustomerProfileResult",
    "GetLossTrendsResult",
    "GetRiskProfileResult",
    # EDW — protocol
    "IEDWReadProvider",
    # Documents — enums
    "DocumentMimeType",
    "DocumentStatus",
    "DocumentType",
    # Documents — models
    "DocumentDetail",
    "DocumentEvidence",
    "DocumentSearchRequest",
    "DocumentSearchResult",
    "DocumentSummary",
    # Documents — results
    "GetDocumentEvidenceResult",
    "GetDocumentResult",
    "GetDocumentsResult",
    "GetDocumentTextResult",
    "SearchDocumentsResult",
    # Documents — protocol
    "IDocumentReadProvider",
    # Fraud — enums
    "FraudIndicatorType",
    "FraudRiskLevel",
    "SIURecommendationStatus",
    # Fraud — models
    "FraudAssessment",
    "FraudIndicator",
    "SIURecommendation",
    # Fraud — results
    "GetFraudIndicatorsResult",
    "GetSIURecommendationResult",
    # Fraud — protocol
    "IFraudReadProvider",
    # Email — enums
    "DraftEmailPurpose",
    "DraftEmailTone",
    "EmailDirection",
    "EmailStatus",
    # Email — models
    "DraftEmailRequest",
    "DraftEmailResult",
    "EmailMessage",
    "EmailSummary",
    "EmailThread",
    # Email — results
    "GetClaimCorrespondenceResult",
    "GetEmailThreadResult",
    # Email — protocols
    "IEmailDraftProvider",
    "IEmailReadProvider",
]
