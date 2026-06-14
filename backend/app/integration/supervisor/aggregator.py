"""
Aggregator — merges multi-provider results into a unified claim intelligence response.

Receives raw ToolResult objects from the executor and produces a structured
dict keyed by provider name. The aggregator is read-only: it inspects results
but never calls provider methods.

Design rules:
  - Each provider's result is included under its provider name key.
  - Failures are represented as {"status": "error", "reason": "..."} entries —
    they do not propagate as exceptions.
  - The aggregator never modifies the original result objects.
  - Email body content retains its UNTRUSTED DATA status (ADR-006). The
    aggregated result includes email metadata only — subjects, thread IDs,
    directions, timestamps. Body text is excluded from the aggregated result
    to prevent untrusted content from appearing in supervisor output where it
    could be mistaken for an instruction.
  - The aggregator produces a serialisable dict (str, int, float, bool, list,
    dict values only — no Pydantic models, no Decimal).

Field names are derived from the Sprint 1 contract models (read with
`vars(instance)` to confirm). Do not assume field names — verify against
the contract source.
"""

from __future__ import annotations

import logging
from typing import Any

from .models import ClaimIntent, ProviderTrace, SupervisorStatus

logger = logging.getLogger(__name__)


def _safe_str(v: Any) -> str | None:
    if v is None:
        return None
    if hasattr(v, "value"):
        return v.value
    return str(v)


def _safe_decimal(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _party_summary(p: Any) -> dict[str, Any] | None:
    if p is None:
        return None
    return {
        "party_id": getattr(p, "party_id", None),
        "display_name": getattr(p, "display_name", None),
        "role": getattr(p, "role", None),
        "email": getattr(p, "email", None),
    }


def _aggregate_claimcenter(result: Any) -> dict[str, Any]:
    # ClaimDetail fields: claim_id, claim_number, policy_number, line_of_business,
    # status, loss_date, reported_date, insured, description, claimant,
    # total_reserves, total_payments, siu_flag, litigation_flag, assigned_adjuster_id
    claim = getattr(result, "claim", None)
    if claim is None:
        return {"status": "not_found"}
    return {
        "status": "success",
        "claim_id": getattr(claim, "claim_id", None),
        "claim_number": getattr(claim, "claim_number", None),
        "claim_status": _safe_str(getattr(claim, "status", None)),
        "line_of_business": _safe_str(getattr(claim, "line_of_business", None)),
        "loss_date": (
            claim.loss_date.isoformat()
            if getattr(claim, "loss_date", None) else None
        ),
        "reported_date": (
            claim.reported_date.isoformat()
            if getattr(claim, "reported_date", None) else None
        ),
        "description": getattr(claim, "description", None),
        "policy_number": getattr(claim, "policy_number", None),
        "insured": _party_summary(getattr(claim, "insured", None)),
        "claimant": _party_summary(getattr(claim, "claimant", None)),
        "siu_flag": getattr(claim, "siu_flag", None),
        "litigation_flag": getattr(claim, "litigation_flag", None),
        "total_reserves": _safe_decimal(
            getattr(getattr(claim, "total_reserves", None), "amount", None)
        ),
        "total_payments": _safe_decimal(
            getattr(getattr(claim, "total_payments", None), "amount", None)
        ),
    }


def _aggregate_policycenter(result: Any) -> dict[str, Any]:
    # Policy fields: policy_id, policy_number, line_of_business, status,
    # effective_date, expiration_date, insured, carrier, program
    policy = getattr(result, "policy", None)
    if policy is None:
        return {"status": "not_found"}
    return {
        "status": "success",
        "policy_id": getattr(policy, "policy_id", None),
        "policy_number": getattr(policy, "policy_number", None),
        "policy_status": _safe_str(getattr(policy, "status", None)),
        "line_of_business": _safe_str(getattr(policy, "line_of_business", None)),
        "effective_date": (
            policy.effective_date.isoformat()
            if getattr(policy, "effective_date", None) else None
        ),
        "expiration_date": (
            policy.expiration_date.isoformat()
            if getattr(policy, "expiration_date", None) else None
        ),
        "carrier": getattr(policy, "carrier", None),
        "program": getattr(policy, "program", None),
    }


def _aggregate_edw(result: Any) -> dict[str, Any]:
    # CustomerProfile fields: customer_id, years_as_customer, lifetime_claims_count,
    # lifetime_claims_paid, open_claims_count, risk_tier, risk_score,
    # policy_count, preferred_contact_method
    profile = getattr(result, "profile", None)
    if profile is None:
        return {"status": "not_found"}
    return {
        "status": "success",
        "customer_id": getattr(profile, "customer_id", None),
        "risk_tier": _safe_str(getattr(profile, "risk_tier", None)),
        "risk_score": _safe_decimal(getattr(profile, "risk_score", None)),
        "years_as_customer": getattr(profile, "years_as_customer", None),
        "lifetime_claims_count": getattr(profile, "lifetime_claims_count", None),
        "open_claims_count": getattr(profile, "open_claims_count", None),
        "policy_count": getattr(profile, "policy_count", None),
    }


def _aggregate_documents(result: Any) -> dict[str, Any]:
    # ClaimDocument fields: document_id, claim_id, document_type, title, status,
    # mime_type, file_size_bytes, page_count, received_date, has_extracted_text
    documents = getattr(result, "documents", None)
    pagination = getattr(result, "pagination", None)
    if documents is None:
        return {"status": "not_found"}
    doc_list = [
        {
            "document_id": getattr(d, "document_id", None),
            "document_type": _safe_str(getattr(d, "document_type", None)),
            "title": getattr(d, "title", None),
            "file_size_bytes": getattr(d, "file_size_bytes", None),
            "page_count": getattr(d, "page_count", None),
            "has_extracted_text": getattr(d, "has_extracted_text", None),
        }
        for d in documents
    ]
    return {
        "status": "success",
        "document_count": (
            pagination.total_records if pagination else len(doc_list)
        ),
        "documents": doc_list,
    }


def _aggregate_fraud(result: Any) -> dict[str, Any]:
    # FraudAssessment fields: assessment_id, claim_id, risk_level, fraud_score,
    # indicators, assessed_at, model_version, siu_recommendation,
    # prior_fraud_flags_on_customer
    assessment = getattr(result, "assessment", None)
    if assessment is None:
        return {"status": "not_found"}
    siu_rec = getattr(assessment, "siu_recommendation", None)
    return {
        "status": "success",
        "assessment_id": getattr(assessment, "assessment_id", None),
        "fraud_score": _safe_decimal(getattr(assessment, "fraud_score", None)),
        "risk_level": _safe_str(getattr(assessment, "risk_level", None)),
        "siu_referral_recommended": (
            siu_rec.value if hasattr(siu_rec, "value") else str(siu_rec)
            if siu_rec is not None else None
        ),
        "prior_fraud_flags": getattr(assessment, "prior_fraud_flags_on_customer", None),
        "indicator_count": (
            len(assessment.indicators) if getattr(assessment, "indicators", None) else 0
        ),
    }


def _aggregate_email(result: Any) -> dict[str, Any]:
    # EmailSummary fields: email_id, claim_id, direction, status, subject,
    # from_party, to_parties, sent_at, thread_id
    emails = getattr(result, "emails", None)
    total_count = getattr(result, "total_count", 0)
    if emails is None:
        return {"status": "not_found"}
    # Email bodies are UNTRUSTED DATA (ADR-006) — only metadata included
    email_list = [
        {
            "email_id": getattr(e, "email_id", None),
            "direction": _safe_str(getattr(e, "direction", None)),
            "subject": getattr(e, "subject", None),
            "from_party": _party_summary(getattr(e, "from_party", None)),
            "sent_at": (
                e.sent_at.isoformat()
                if getattr(e, "sent_at", None) else None
            ),
            "thread_id": getattr(e, "thread_id", None),
        }
        for e in emails
    ]
    return {
        "status": "success",
        "total_count": total_count,
        # Body text excluded — UNTRUSTED DATA per ADR-006
        "emails_metadata": email_list,
    }


_PROVIDER_AGGREGATORS = {
    "claimcenter":  _aggregate_claimcenter,
    "policycenter": _aggregate_policycenter,
    "edw":          _aggregate_edw,
    "documents":    _aggregate_documents,
    "fraud":        _aggregate_fraud,
    "email":        _aggregate_email,
}


def aggregate(
    intent: ClaimIntent,
    traces: list[ProviderTrace],
    raw_results: dict[str, Any],
) -> tuple[dict[str, Any], SupervisorStatus]:
    """
    Merge per-provider results into a unified aggregated response.

    Args:
        intent:       The intent that drove provider selection.
        traces:       Execution trace list from the executor.
        raw_results:  {provider_name: raw ToolResult} from the executor.

    Returns:
        (aggregated_dict, SupervisorStatus)
    """
    aggregated: dict[str, Any] = {"intent": intent.value, "providers": {}}

    succeeded = 0
    failed = 0

    for trace in traces:
        name = trace.provider
        raw = raw_results.get(name)

        if raw is None:
            aggregated["providers"][name] = {
                "status": "error",
                "reason": trace.error_message or "Provider call failed",
            }
            failed += 1
            continue

        aggregator_fn = _PROVIDER_AGGREGATORS.get(name)
        if aggregator_fn is None:
            aggregated["providers"][name] = {"status": "unsupported_provider"}
            failed += 1
            continue

        try:
            aggregated["providers"][name] = aggregator_fn(raw)
            succeeded += 1
        except Exception as exc:
            logger.warning("Aggregator: error processing %s: %s", name, exc)
            aggregated["providers"][name] = {
                "status": "aggregation_error",
                "reason": type(exc).__name__,
            }
            failed += 1

    # Determine overall status
    if succeeded == 0:
        overall = SupervisorStatus.FAILED
    elif failed > 0:
        overall = SupervisorStatus.PARTIAL
    else:
        overall = SupervisorStatus.SUCCESS

    return aggregated, overall
