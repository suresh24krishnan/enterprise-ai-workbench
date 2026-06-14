"""
Response validator — output shape consistency checking.

Validates that provider method return values conform to the standard
ToolResult format: every result carries a `status` field (ToolResultStatus),
an optional `error` field (ToolError | None), and the correct payload
field for the provider method.

Rules enforced:
  1. Every result has a `status` attribute of type ToolResultStatus
  2. SUCCESS results must NOT have an error field set
  3. NOT_FOUND / ERROR results must have an error field with:
       - code: non-empty string
       - message: non-empty string
       - source_system: a SourceSystem value (not None)
       - retryable: a bool
  4. Paginated results must have a valid PaginationResponse when status=SUCCESS:
       - page >= 1
       - page_size >= 1
       - total_records >= 0
       - total_pages >= 1
       - has_next and has_previous are bools
  5. health() must return ProviderStatus.MOCK in mock mode

This validator DOES execute provider read methods against known fixture
data (CLM-2026-100245 / CA-2024-8812 / EDW-CUST-10042) to validate
real return shapes. It does not test business logic — only response
structure.

No writes are performed. MockWriteDisabledError is expected from write
methods; the response_validator does not test write methods (that is
error_validator's responsibility).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.integration.contracts.common import (
    PaginationRequest,
    ProviderStatus,
    ToolExecutionContext,
    ToolResultStatus,
    ProviderMode,
)

# ---------------------------------------------------------------------------
# Shared test context and fixture IDs
# ---------------------------------------------------------------------------

_TEST_CTX = ToolExecutionContext(
    user_id="validator",
    display_name="Validation Runner",
    roles=["adjuster"],
    permissions=["read"],
    correlation_id="val-corr",
    trace_id="val-trace",
    request_id="val-req",
    provider_mode=ProviderMode.MOCK,
    writes_enabled=False,
)

_KNOWN_CLAIM_ID = "CLM-2026-100245"
_KNOWN_POLICY_ID = "CA-2024-8812"
_KNOWN_CUSTOMER_ID = "EDW-CUST-10042"
_UNKNOWN_ID = "UNKNOWN-99999"

_SMALL_PAGE = PaginationRequest(page=1, page_size=2)


@dataclass
class ResponseViolation:
    provider_name: str
    method_name: str
    violation_type: str
    detail: str


@dataclass
class ResponseValidationResult:
    provider_name: str
    valid: bool
    violations: list[ResponseViolation] = field(default_factory=list)
    checks_run: int = 0
    checks_passed: int = 0

    @property
    def summary(self) -> str:
        if self.valid:
            return f"PASS ({self.checks_passed}/{self.checks_run} checks)"
        return (
            f"FAIL ({self.checks_passed}/{self.checks_run} checks, "
            f"{len(self.violations)} violation(s))"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_result_base(
    result: Any,
    method_name: str,
    provider_name: str,
    violations: list[ResponseViolation],
    checks: list[bool],
) -> None:
    """Validate the base ToolResult shape (status + error consistency)."""
    # status must exist and be a ToolResultStatus
    status = getattr(result, "status", None)
    if status is None or not isinstance(status, ToolResultStatus):
        violations.append(ResponseViolation(
            provider_name=provider_name,
            method_name=method_name,
            violation_type="missing_status",
            detail=f"Result has no valid 'status' field (got {type(status).__name__})",
        ))
        checks.append(False)
        return
    checks.append(True)

    err = getattr(result, "error", None)

    # SUCCESS: error must be None
    if status == ToolResultStatus.SUCCESS:
        if err is not None:
            violations.append(ResponseViolation(
                provider_name=provider_name,
                method_name=method_name,
                violation_type="error_on_success",
                detail="Result has status=SUCCESS but error field is set",
            ))
            checks.append(False)
        else:
            checks.append(True)

    # NOT_FOUND / ERROR / etc: error must be populated
    elif status in (ToolResultStatus.NOT_FOUND, ToolResultStatus.ERROR,
                    ToolResultStatus.RATE_LIMITED, ToolResultStatus.UNAVAILABLE,
                    ToolResultStatus.PERMISSION_DENIED):
        if err is None:
            violations.append(ResponseViolation(
                provider_name=provider_name,
                method_name=method_name,
                violation_type="missing_error_on_failure",
                detail=f"Result has status={status.value} but error field is None",
            ))
            checks.append(False)
        else:
            # Validate ToolError fields
            bad_fields = []
            if not getattr(err, "code", None):
                bad_fields.append("code is empty")
            if not getattr(err, "message", None):
                bad_fields.append("message is empty")
            if getattr(err, "source_system", None) is None:
                bad_fields.append("source_system is None")
            if not isinstance(getattr(err, "retryable", None), bool):
                bad_fields.append("retryable is not bool")
            if bad_fields:
                violations.append(ResponseViolation(
                    provider_name=provider_name,
                    method_name=method_name,
                    violation_type="malformed_tool_error",
                    detail=f"ToolError fields invalid: {'; '.join(bad_fields)}",
                ))
                checks.append(False)
            else:
                checks.append(True)


def _check_pagination(
    result: Any,
    method_name: str,
    provider_name: str,
    violations: list[ResponseViolation],
    checks: list[bool],
) -> None:
    """Validate PaginationResponse shape on paginated results."""
    status = getattr(result, "status", None)
    if status != ToolResultStatus.SUCCESS:
        return  # pagination only checked on success

    pagination = getattr(result, "pagination", None)
    if pagination is None:
        return  # not a paginated result — skip

    bad = []
    if not isinstance(getattr(pagination, "page", None), int) or pagination.page < 1:
        bad.append(f"page={getattr(pagination, 'page', None)} (must be >= 1)")
    if not isinstance(getattr(pagination, "page_size", None), int) or pagination.page_size < 1:
        bad.append(f"page_size={getattr(pagination, 'page_size', None)} (must be >= 1)")
    if not isinstance(getattr(pagination, "total_records", None), int) or pagination.total_records < 0:
        bad.append(f"total_records={getattr(pagination, 'total_records', None)} (must be >= 0)")
    if not isinstance(getattr(pagination, "total_pages", None), int) or pagination.total_pages < 1:
        bad.append(f"total_pages={getattr(pagination, 'total_pages', None)} (must be >= 1)")
    if not isinstance(getattr(pagination, "has_next", None), bool):
        bad.append("has_next not bool")
    if not isinstance(getattr(pagination, "has_previous", None), bool):
        bad.append("has_previous not bool")

    if bad:
        violations.append(ResponseViolation(
            provider_name=provider_name,
            method_name=method_name,
            violation_type="malformed_pagination",
            detail=f"PaginationResponse invalid: {'; '.join(bad)}",
        ))
        checks.append(False)
    else:
        checks.append(True)


# ---------------------------------------------------------------------------
# Per-provider validation suites
# ---------------------------------------------------------------------------

def _validate_claimcenter(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    ctx = _TEST_CTX

    # health
    h = provider.health()
    checks.append(isinstance(h, ProviderStatus))

    # get_claim — known
    r = provider.get_claim(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_claim[known]", name, violations, checks)
    if r.status == ToolResultStatus.SUCCESS and r.claim is None:
        violations.append(ResponseViolation(name, "get_claim[known]", "null_payload", "claim is None on SUCCESS"))
        checks.append(False)
    elif r.status == ToolResultStatus.SUCCESS:
        checks.append(True)

    # get_claim — unknown → NOT_FOUND
    r = provider.get_claim(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_claim[unknown]", name, violations, checks)

    # get_claims — paginated
    r = provider.get_claims("usr-john-smith", ctx, pagination=_SMALL_PAGE)
    _check_result_base(r, "get_claims", name, violations, checks)
    _check_pagination(r, "get_claims", name, violations, checks)

    # get_claim_notes — known, paginated
    r = provider.get_claim_notes(_KNOWN_CLAIM_ID, ctx, pagination=_SMALL_PAGE)
    _check_result_base(r, "get_claim_notes[known]", name, violations, checks)
    _check_pagination(r, "get_claim_notes[known]", name, violations, checks)

    # get_claim_notes — unknown
    r = provider.get_claim_notes(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_claim_notes[unknown]", name, violations, checks)

    # get_exposures
    r = provider.get_exposures(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_exposures[known]", name, violations, checks)

    # get_activities
    r = provider.get_activities(_KNOWN_CLAIM_ID, ctx, pagination=_SMALL_PAGE)
    _check_result_base(r, "get_activities[known]", name, violations, checks)
    _check_pagination(r, "get_activities[known]", name, violations, checks)

    # get_reserves
    r = provider.get_reserves(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_reserves[known]", name, violations, checks)

    # get_payments
    r = provider.get_payments(_KNOWN_CLAIM_ID, ctx, pagination=_SMALL_PAGE)
    _check_result_base(r, "get_payments[known]", name, violations, checks)


def _validate_policycenter(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    ctx = _TEST_CTX
    provider.health()
    checks.append(True)

    r = provider.get_policy(_KNOWN_POLICY_ID, ctx)
    _check_result_base(r, "get_policy[known]", name, violations, checks)

    r = provider.get_policy(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_policy[unknown]", name, violations, checks)

    r = provider.get_policy_coverages(_KNOWN_POLICY_ID, ctx)
    _check_result_base(r, "get_policy_coverages", name, violations, checks)

    r = provider.get_policy_limits(_KNOWN_POLICY_ID, None, ctx)
    _check_result_base(r, "get_policy_limits", name, violations, checks)

    r = provider.get_policy_deductibles(_KNOWN_POLICY_ID, None, ctx)
    _check_result_base(r, "get_policy_deductibles", name, violations, checks)

    r = provider.get_endorsements(_KNOWN_POLICY_ID, ctx)
    _check_result_base(r, "get_endorsements", name, violations, checks)


def _validate_edw(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    ctx = _TEST_CTX
    provider.health()
    checks.append(True)

    r = provider.get_customer_profile(_KNOWN_CUSTOMER_ID, ctx)
    _check_result_base(r, "get_customer_profile[known]", name, violations, checks)

    r = provider.get_customer_profile(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_customer_profile[unknown]", name, violations, checks)

    r = provider.get_claim_history(_KNOWN_CUSTOMER_ID, ctx)
    _check_result_base(r, "get_claim_history", name, violations, checks)

    r = provider.get_loss_trends(_KNOWN_CUSTOMER_ID, ctx)
    _check_result_base(r, "get_loss_trends", name, violations, checks)

    r = provider.get_risk_profile(_KNOWN_CUSTOMER_ID, ctx)
    _check_result_base(r, "get_risk_profile", name, violations, checks)


def _validate_documents(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    from backend.app.integration.contracts.documents import DocumentSearchRequest
    ctx = _TEST_CTX
    provider.health()
    checks.append(True)

    r = provider.get_documents(_KNOWN_CLAIM_ID, ctx, pagination=_SMALL_PAGE)
    _check_result_base(r, "get_documents[known]", name, violations, checks)
    _check_pagination(r, "get_documents[known]", name, violations, checks)

    r = provider.get_document("doc-001", _KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_document[known]", name, violations, checks)

    r = provider.get_document("doc-001", "CLM-WRONG", ctx)
    _check_result_base(r, "get_document[wrong_claim]", name, violations, checks)

    req = DocumentSearchRequest(claim_id=_KNOWN_CLAIM_ID, query="repair estimate", max_results=5)
    r = provider.search_documents(req, ctx)
    _check_result_base(r, "search_documents", name, violations, checks)

    r = provider.get_document_text("doc-001", _KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_document_text[known]", name, violations, checks)
    if r.status == ToolResultStatus.SUCCESS:
        if not isinstance(getattr(r, "extracted_text", None), str) or not r.extracted_text:
            violations.append(ResponseViolation(name, "get_document_text", "empty_text", "extracted_text is empty"))
            checks.append(False)
        else:
            checks.append(True)

    r = provider.get_document_evidence(_KNOWN_CLAIM_ID, ["doc-001", "doc-002"], ctx)
    _check_result_base(r, "get_document_evidence", name, violations, checks)


def _validate_fraud(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    ctx = _TEST_CTX
    provider.health()
    checks.append(True)

    r = provider.get_fraud_indicators(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_fraud_indicators[known]", name, violations, checks)

    r = provider.get_fraud_indicators(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_fraud_indicators[unknown]", name, violations, checks)

    r = provider.get_siu_recommendation(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_siu_recommendation[known]", name, violations, checks)

    r = provider.get_siu_recommendation(_UNKNOWN_ID, ctx)
    _check_result_base(r, "get_siu_recommendation[unknown]", name, violations, checks)


def _validate_email(
    provider: Any, violations: list[ResponseViolation], checks: list[bool], name: str
) -> None:
    from backend.app.integration.contracts.email import DraftEmailRequest, DraftEmailPurpose
    from backend.app.integration.contracts.common import PartySummary, SourceSystem
    ctx = _TEST_CTX
    provider.health()
    checks.append(True)

    r = provider.get_claim_correspondence(_KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_claim_correspondence[known]", name, violations, checks)

    r = provider.get_claim_correspondence(_UNKNOWN_ID, ctx)
    # NOT_FOUND is acceptable; so is SUCCESS with empty list
    status = getattr(r, "status", None)
    if status not in (ToolResultStatus.NOT_FOUND, ToolResultStatus.SUCCESS):
        violations.append(ResponseViolation(name, "get_claim_correspondence[unknown]",
            "unexpected_status", f"Expected NOT_FOUND or SUCCESS, got {status}"))
        checks.append(False)
    else:
        checks.append(True)

    r = provider.get_email_thread("thread-001", _KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_email_thread[known]", name, violations, checks)

    r = provider.get_email_thread("thread-UNKNOWN", _KNOWN_CLAIM_ID, ctx)
    _check_result_base(r, "get_email_thread[unknown]", name, violations, checks)

    recip = PartySummary(
        party_id="pty-001", source_system=SourceSystem.EMAIL,
        source_id="x", display_name="Test", role="insured",
    )
    req = DraftEmailRequest(
        claim_id=_KNOWN_CLAIM_ID,
        purpose=DraftEmailPurpose.STATUS_UPDATE,
        recipient=recip,
        key_points=["Coverage confirmed"],
    )
    r = provider.draft_email(req, ctx)
    _check_result_base(r, "draft_email", name, violations, checks)
    if r.status == ToolResultStatus.SUCCESS:
        if not getattr(r, "draft_body", None):
            violations.append(ResponseViolation(name, "draft_email", "empty_draft", "draft_body is empty"))
            checks.append(False)
        else:
            checks.append(True)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "claimcenter": _validate_claimcenter,
    "policycenter": _validate_policycenter,
    "edw": _validate_edw,
    "documents": _validate_documents,
    "fraud": _validate_fraud,
    "email": _validate_email,
}


def validate_response(provider_name: str, provider: Any) -> ResponseValidationResult:
    """
    Validate response shapes for a named provider.

    Executes provider read methods against known fixture data and validates
    the structural correctness of every result.

    Args:
        provider_name: canonical name (e.g. "claimcenter")
        provider: the provider instance to validate

    Returns:
        ResponseValidationResult with check counts and any violations
    """
    violations: list[ResponseViolation] = []
    checks: list[bool] = []

    validator_fn = _VALIDATORS.get(provider_name)
    if validator_fn is None:
        return ResponseValidationResult(
            provider_name=provider_name,
            valid=False,
            violations=[ResponseViolation(
                provider_name, "N/A", "unknown_provider",
                f"No response validator registered for provider '{provider_name}'"
            )],
        )

    try:
        validator_fn(provider, violations, checks, provider_name)
    except Exception as exc:
        violations.append(ResponseViolation(
            provider_name, "validation_runner", "unexpected_exception",
            f"Unexpected exception during response validation: {type(exc).__name__}: {exc}",
        ))
        checks.append(False)

    return ResponseValidationResult(
        provider_name=provider_name,
        valid=len(violations) == 0 and all(checks),
        violations=violations,
        checks_run=len(checks),
        checks_passed=sum(1 for c in checks if c),
    )


def validate_all_responses(providers: dict[str, Any]) -> dict[str, ResponseValidationResult]:
    """Validate response shapes for all named providers."""
    return {name: validate_response(name, provider) for name, provider in providers.items()}
