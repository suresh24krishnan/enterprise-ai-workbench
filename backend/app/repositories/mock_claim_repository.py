"""
MockClaimRepository — Phase 1 in-memory implementation of IClaimRepository.

All data is defined here. Nothing is read from a database or external API.
This is the only file that changes when moving to a real ClaimCenter adapter.
"""

from __future__ import annotations

import uuid

_CLAIM_ID = "CLM-2026-100245"

# ---------------------------------------------------------------------------
# Mock claim list (index view)
# ---------------------------------------------------------------------------

_CLAIMS_LIST = [
    {
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "status": "OPEN",
        "type": "AUTO_LIABILITY",
        "risk_level": "MEDIUM",
        "date_of_loss": "2026-06-08",
        "reserve_amount": 8450.00,
        "primary_insured_name": "ABC Logistics Inc.",
    }
]

# ---------------------------------------------------------------------------
# Mock claim detail
# ---------------------------------------------------------------------------

_CLAIM_DETAIL = {
    "claim_id": _CLAIM_ID,
    "claim_number": _CLAIM_ID,
    "status": "OPEN",
    "type": "AUTO_LIABILITY",
    "risk_level": "MEDIUM",
    "date_of_loss": "2026-06-08",
    "reported_at": "2026-06-08T14:32:00Z",
    "description": (
        "Rear-end collision at I-75 & Exit 42, Miami, FL. "
        "Insured vehicle (2023 Freightliner Cascadia, plate FL-LGT-8821) struck from behind "
        "by third-party vehicle while stopped at traffic signal. "
        "Minor injuries reported; driver M. Torres is ambulatory."
    ),
    "reserve_amount": 8450.00,
    "paid_amount": 0.00,
    "litigation_flag": False,
    "jurisdiction_code": "FL",
    "parties": [
        {
            "party_id": "pty-001",
            "role": "INSURED",
            "name": "ABC Logistics Inc.",
            "contact_phone": "305-555-0192",
            "contact_email": "claims@abclogistics.local",
            "represented_by": None,
        },
        {
            "party_id": "pty-002",
            "role": "CLAIMANT",
            "name": "Marcus Torres",
            "contact_phone": "305-555-0347",
            "contact_email": None,
            "represented_by": None,
        },
    ],
    "coverages": [
        {
            "coverage_id": "cov-001",
            "coverage_type": "Bodily Injury Liability",
            "limit": 1000000.00,
            "deductible": 5000.00,
            "is_applicable": True,
        },
        {
            "coverage_id": "cov-002",
            "coverage_type": "Physical Damage – Collision",
            "limit": 250000.00,
            "deductible": 2500.00,
            "is_applicable": True,
        },
        {
            "coverage_id": "cov-003",
            "coverage_type": "Rental Reimbursement",
            "limit": 2250.00,   # $75/day × 30 days
            "deductible": 0.00,
            "is_applicable": True,
        },
    ],
    "notes": [
        {
            "note_id": "nte-001",
            "content": "Initial contact with insured. Confirmed coverage active. Vehicle towed to Riverside Auto Body.",
            "author": "John Smith",
            "authored_at": "2026-06-08T16:00:00Z",
            "is_ai_generated": False,
            "approved_by": None,
            "approved_at": None,
        }
    ],
    "documents": [
        {"document_id": "doc-001", "title": "Police Report – Incident #MIA-2026-88421", "document_type": "POLICE_REPORT", "uploaded_at": "2026-06-09T08:00:00Z", "uploaded_by": "John Smith"},
        {"document_id": "doc-002", "title": "Repair Estimate – Riverside Auto Body", "document_type": "REPAIR_ESTIMATE", "uploaded_at": "2026-06-10T11:30:00Z", "uploaded_by": "John Smith"},
        {"document_id": "doc-003", "title": "Claim Report – ABC Logistics Fleet", "document_type": "CLAIM_REPORT", "uploaded_at": "2026-06-08T15:00:00Z", "uploaded_by": "System"},
        {"document_id": "doc-004", "title": "Photos – Vehicle Damage (8 images)", "document_type": "PHOTOS", "uploaded_at": "2026-06-09T09:15:00Z", "uploaded_by": "John Smith"},
        {"document_id": "doc-005", "title": "Rental Request – Enterprise Rent-A-Car", "document_type": "RENTAL_REQUEST", "uploaded_at": "2026-06-09T10:00:00Z", "uploaded_by": "M. Torres"},
    ],
}

# ---------------------------------------------------------------------------
# Mock evidence sources (7 sources, as specified)
# ---------------------------------------------------------------------------

_EVIDENCE_SOURCES = [
    {
        "source_id": "src-001",
        "source_type": "CLAIM_DOCUMENT",
        "title": "Police Report – Incident #MIA-2026-88421",
        "excerpt": (
            "Officer on scene confirmed rear-end collision. Third-party driver cited for "
            "failure to maintain safe following distance (FL Statute 316.0895). "
            "No DUI involvement. All parties ambulatory at scene."
        ),
        "relevance_score": 0.97,
        "document_id": "doc-001",
        "page_reference": "Page 1, Section: Narrative",
        "retrieved_at": "2026-06-13T10:01:05Z",
    },
    {
        "source_id": "src-002",
        "source_type": "CLAIM_DOCUMENT",
        "title": "Repair Estimate – Riverside Auto Body",
        "excerpt": (
            "Total repair estimate: $6,200.00. Damage to rear bumper assembly, trailer hitch, "
            "and rear lighting cluster. Parts: $3,800. Labor: $2,400. "
            "Estimated repair time: 5–7 business days."
        ),
        "relevance_score": 0.95,
        "document_id": "doc-002",
        "page_reference": "Page 1, Line Items",
        "retrieved_at": "2026-06-13T10:01:05Z",
    },
    {
        "source_id": "src-003",
        "source_type": "CLAIM_DOCUMENT",
        "title": "Claim Report – ABC Logistics Fleet",
        "excerpt": (
            "Driver M. Torres reported incident at 14:15 local time. Vehicle was stationary "
            "at red light. Impact from behind at estimated 25–30 mph. Driver reported neck "
            "stiffness post-incident; declined ambulance, sought own medical care."
        ),
        "relevance_score": 0.93,
        "document_id": "doc-003",
        "page_reference": "Section 2: Incident Details",
        "retrieved_at": "2026-06-13T10:01:06Z",
    },
    {
        "source_id": "src-004",
        "source_type": "POLICY_DOCUMENT",
        "title": "Commercial Auto Policy #CA-2024-8812 – Section 4.2",
        "excerpt": (
            "Section 4.2 – Bodily Injury Liability: Coverage applies to bodily injury "
            "sustained by any person caused by an accident resulting from the ownership, "
            "maintenance, or use of a covered auto. Per occurrence limit: $1,000,000. "
            "Deductible: $5,000."
        ),
        "relevance_score": 0.91,
        "document_id": None,
        "page_reference": "Page 14, Section 4.2",
        "retrieved_at": "2026-06-13T10:01:06Z",
    },
    {
        "source_id": "src-005",
        "source_type": "CLAIM_DOCUMENT",
        "title": "Photos – Vehicle Damage (8 images)",
        "excerpt": (
            "Image analysis: Visible crumple damage to rear bumper and hitch receiver. "
            "Rear tail light assembly shattered (left side). Consistent with low-speed "
            "rear-end impact. No frame damage visible in submitted photographs."
        ),
        "relevance_score": 0.88,
        "document_id": "doc-004",
        "page_reference": "Images 1–4 of 8",
        "retrieved_at": "2026-06-13T10:01:07Z",
    },
    {
        "source_id": "src-006",
        "source_type": "CLAIM_NOTE",
        "title": "Claim Notes – Initial Adjuster Contact",
        "excerpt": (
            "Confirmed insured coverage active as of date of loss. Fleet policy in good "
            "standing; no lapse. Vehicle was listed on schedule of autos. "
            "Tow to Riverside Auto Body authorized."
        ),
        "relevance_score": 0.85,
        "document_id": None,
        "page_reference": "Note dated 2026-06-08",
        "retrieved_at": "2026-06-13T10:01:07Z",
    },
    {
        "source_id": "src-007",
        "source_type": "CLAIM_DOCUMENT",
        "title": "Rental Request – Enterprise Rent-A-Car",
        "excerpt": (
            "Insured requested rental vehicle for business operations continuity. "
            "Policy provides $75/day up to 30 days. Rental begins 2026-06-09. "
            "Estimated rental cost: $750 (10 days at $75/day)."
        ),
        "relevance_score": 0.82,
        "document_id": "doc-005",
        "page_reference": "Rental Authorization Form",
        "retrieved_at": "2026-06-13T10:01:08Z",
    },
]

# ---------------------------------------------------------------------------
# Mock governance decision (embedded in summary)
# ---------------------------------------------------------------------------

_GOVERNANCE_DECISION = {
    "decision_id": "gov-001",
    "evaluated_at": "2026-06-13T10:01:00Z",
    "task_type": "claim_summary",
    "claim_id": _CLAIM_ID,
    "outcome": "ALLOW",
    "reason": "Request is within policy for task type 'claim_summary'. User role ADJUSTER has 'ai:generate' permission. Claim risk level MEDIUM does not trigger escalation threshold.",
    "deny_reason": None,
    "escalate_reason": None,
    "policy_evaluations": [
        {
            "policy_id": "base_policy",
            "policy_version": "1.0",
            "rule_id": "require_ai_generate_permission",
            "matched": True,
            "outcome": "ALLOW",
            "reason": "User has 'ai:generate' permission.",
        },
        {
            "policy_id": "claim_summary_policy",
            "policy_version": "1.0",
            "rule_id": "allow_all_risk_levels_for_summary",
            "matched": True,
            "outcome": "ALLOW",
            "reason": "Summary generation is permitted for all claim risk levels.",
        },
    ],
    "policy_set_id": "mvp_policy_set",
    "policy_set_version": "1.0",
}

# ---------------------------------------------------------------------------
# Mock model routing decision (embedded in summary)
# ---------------------------------------------------------------------------

_MODEL_ROUTE_DECISION = {
    "route_id": "rte-001",
    "decided_at": "2026-06-13T10:01:01Z",
    "task_type": "claim_summary",
    "model_id": "mock-standard",
    "model_tier": "MOCK",
    "provider_id": "mock",
    "routing_reason": "TASK_TYPE_DEFAULT",
    "routing_rationale": "Task type 'claim_summary' routes to standard model tier. Claim risk level MEDIUM does not trigger premium model escalation.",
    "claim_risk_level": "MEDIUM",
    "estimated_cost": 0.00,
    "actual_cost": 0.00,
    "primary_model_id": None,
    "fallback_reason": None,
}

# ---------------------------------------------------------------------------
# Mock claim summary
# ---------------------------------------------------------------------------

_CLAIM_SUMMARY = {
    "summary_id": "sum-001",
    "claim_id": _CLAIM_ID,
    "generated_at": "2026-06-13T10:01:10Z",

    "summary": (
        "On June 8, 2026, a 2023 Freightliner Cascadia operated by ABC Logistics Inc. "
        "was struck from behind while stationary at a red light at I-75 & Exit 42, Miami, FL. "
        "The at-fault third party has been cited by police (FL Statute 316.0895). "
        "Driver M. Torres reported neck stiffness and sought independent medical evaluation. "
        "The vehicle sustained rear bumper and lighting damage estimated at $6,200. "
        "Coverage under Commercial Auto Policy #CA-2024-8812 is confirmed active and applicable."
    ),

    "coverage_analysis": (
        "Bodily Injury Liability (limit $1,000,000 / deductible $5,000) applies to any "
        "third-party injury claims arising from this incident. "
        "Physical Damage – Collision coverage (limit $250,000 / deductible $2,500) applies "
        "to the $6,200 repair estimate; net exposure after deductible is $3,700. "
        "Rental Reimbursement coverage provides up to $75/day for 30 days ($2,250 max); "
        "estimated rental usage of 10 days yields a $750 exposure. "
        "Total current reserve exposure: $8,450."
    ),

    "key_findings": [
        "Third party cited at scene — clear liability established by police report.",
        "Repair estimate of $6,200 is consistent with photographic evidence of damage.",
        "Driver reported neck stiffness — medical treatment status unconfirmed; BI exposure possible.",
        "Rental reimbursement authorized; rental period estimated at 10 days.",
        "No frame damage identified in submitted photos — total loss risk is low.",
        "Fleet policy in good standing; no coverage gap issues.",
    ],

    "open_issues": [
        "Medical treatment records for M. Torres not yet received.",
        "Third-party insurer has not been identified or contacted.",
        "Subrogation potential against at-fault driver not yet evaluated.",
        "Final repair invoice pending completion of repairs.",
    ],

    "recommended_actions": [
        "Obtain medical authorization and records from M. Torres within 14 days.",
        "Identify and contact third-party insurer to pursue subrogation.",
        "Confirm repair completion and obtain final invoice from Riverside Auto Body.",
        "Schedule vehicle inspection if repair cost increases above estimate.",
        "Close rental upon vehicle return and reconcile rental invoice against policy limit.",
    ],

    "risk_indicators": [
        "Bodily injury claim possible — driver sought independent medical care.",
        "Subrogation recovery likely given clear third-party liability citation.",
        "Reserve adequacy: current reserve of $8,450 may require adjustment if BI claim develops.",
    ],

    "evidence_score": 96,
    "confidence_score": 0.94,
    "confidence_rationale": (
        "High confidence based on corroborating evidence across 7 sources: police report "
        "establishes liability, repair estimate is documented and photo-consistent, "
        "policy coverage confirmed active. Primary uncertainty is unresolved BI exposure."
    ),
    "sources_used": 7,

    "evidence_sources": _EVIDENCE_SOURCES,
    "governance_decision": _GOVERNANCE_DECISION,
    "model_route_decision": _MODEL_ROUTE_DECISION,
}

# ---------------------------------------------------------------------------
# Mock audit events (11 events covering 09:58–10:04 UTC)
# Each event carries new fields (actor_type, actor_name, status, description,
# evidence_count, confidence, policy_set, routing_reason) alongside the
# original fields so existing consumers continue to work unchanged.
# ---------------------------------------------------------------------------

_AUDIT_EVENTS = [
    {
        "event_id": "evt-001",
        "event_type": "user.login",
        "actor_type": "USER",
        "actor_name": "John Smith",
        "status": "INFO",
        "description": "Adjuster John Smith authenticated via mock identity provider. Session sess-mock-001 established.",
        "occurred_at": "2026-06-13T09:58:00Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": None,
        "claim_number": None,
        "payload": {
            "identity_provider": "mock",
            "ip_address": "192.168.1.10",
        },
        "governance_decision_id": None,
        "governance_outcome": None,
        "model_id": None,
        "task_type": None,
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": None,
        "evidence_count": None,
        "confidence": None,
        "policy_set": None,
        "routing_reason": None,
    },
    {
        "event_id": "evt-002",
        "event_type": "claim.selected",
        "actor_type": "USER",
        "actor_name": "John Smith",
        "status": "INFO",
        "description": "Adjuster opened claim CLM-2026-100245 (AUTO_LIABILITY, risk: MEDIUM). Claim data loaded from repository.",
        "occurred_at": "2026-06-13T10:00:45Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "claim_status": "OPEN",
            "claim_type": "AUTO_LIABILITY",
            "risk_level": "MEDIUM",
        },
        "governance_decision_id": None,
        "governance_outcome": None,
        "model_id": None,
        "task_type": None,
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": None,
        "evidence_count": None,
        "confidence": None,
        "policy_set": None,
        "routing_reason": None,
    },
    {
        "event_id": "evt-003",
        "event_type": "governance.evaluated",
        "actor_type": "GOVERNANCE",
        "actor_name": "Policy Engine",
        "status": "ALLOW",
        "description": "Governance engine evaluated task 'claim_summary'. 2 policy rules checked. Outcome: ALLOW — user role ADJUSTER has ai:generate permission; risk level MEDIUM does not trigger escalation.",
        "occurred_at": "2026-06-13T10:01:00Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "task_type": "claim_summary",
            "rules_evaluated": 2,
            "rules_matched": 2,
        },
        "governance_decision_id": "gov-001",
        "governance_outcome": "ALLOW",
        "model_id": None,
        "task_type": "claim_summary",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 12,
        "evidence_count": None,
        "confidence": None,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-004",
        "event_type": "ai.rag.retrieved",
        "actor_type": "AI",
        "actor_name": "RAG Engine",
        "status": "SUCCESS",
        "description": "Vector search retrieved 7 evidence sources from claim corpus. Top relevance: 0.97 (Police Report #MIA-2026-88421).",
        "occurred_at": "2026-06-13T10:01:05Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "query": "claim summary for CLM-2026-100245",
            "sources_retrieved": 7,
            "top_relevance_score": 0.97,
        },
        "governance_decision_id": None,
        "governance_outcome": None,
        "model_id": None,
        "task_type": "claim_summary",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 38,
        "evidence_count": 7,
        "confidence": None,
        "policy_set": None,
        "routing_reason": None,
    },
    {
        "event_id": "evt-005",
        "event_type": "model.routed",
        "actor_type": "SYSTEM",
        "actor_name": "Model Router",
        "status": "INFO",
        "description": "Task 'claim_summary' routed to mock-standard (MOCK tier). Risk level MEDIUM does not trigger premium model escalation.",
        "occurred_at": "2026-06-13T10:01:07Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "model_tier": "MOCK",
            "provider": "mock",
        },
        "governance_decision_id": None,
        "governance_outcome": None,
        "model_id": "mock-standard",
        "task_type": "claim_summary",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 5,
        "evidence_count": None,
        "confidence": None,
        "policy_set": None,
        "routing_reason": "TASK_TYPE_DEFAULT",
    },
    {
        "event_id": "evt-006",
        "event_type": "ai.summary.generated",
        "actor_type": "AI",
        "actor_name": "mock-standard",
        "status": "SUCCESS",
        "description": "AI generated claim summary using 7 evidence sources. Confidence: 94%. Evidence score: 96/100. Output grounded in police report, repair estimate, and policy document.",
        "occurred_at": "2026-06-13T10:01:10Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "summary_id": "sum-001",
            "evidence_score": 96,
            "sources_used": 7,
        },
        "governance_decision_id": "gov-001",
        "governance_outcome": "ALLOW",
        "model_id": "mock-standard",
        "task_type": "claim_summary",
        "input_tokens": 1840,
        "output_tokens": 512,
        "latency_ms": 245,
        "evidence_count": 7,
        "confidence": 0.94,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-007",
        "event_type": "governance.evaluated",
        "actor_type": "GOVERNANCE",
        "actor_name": "Policy Engine",
        "status": "ALLOW",
        "description": "Governance engine evaluated task 'claim_assistant'. 2 policy rules checked. Outcome: ALLOW — query is grounded in authorized claim evidence for CLM-2026-100245.",
        "occurred_at": "2026-06-13T10:02:00Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "task_type": "claim_assistant",
            "rules_evaluated": 2,
            "rules_matched": 2,
        },
        "governance_decision_id": "gov-conv-001",
        "governance_outcome": "ALLOW",
        "model_id": None,
        "task_type": "claim_assistant",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 8,
        "evidence_count": None,
        "confidence": None,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-008",
        "event_type": "ai.conversation.turn_completed",
        "actor_type": "AI",
        "actor_name": "mock-standard",
        "status": "SUCCESS",
        "description": "AI assistant responded to query 'What are the outstanding issues?'. Response grounded in 3 evidence sources. Confidence: 92%.",
        "occurred_at": "2026-06-13T10:02:05Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "intent": "outstanding_issues",
            "sources_used": 3,
        },
        "governance_decision_id": "gov-conv-001",
        "governance_outcome": "ALLOW",
        "model_id": "mock-standard",
        "task_type": "claim_assistant",
        "input_tokens": 924,
        "output_tokens": 287,
        "latency_ms": 183,
        "evidence_count": 3,
        "confidence": 0.92,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-009",
        "event_type": "ai.note.drafted",
        "actor_type": "AI",
        "actor_name": "mock-standard",
        "status": "SUCCESS",
        "description": "AI generated draft adjuster note (draft-001) using 4 evidence sources. Confidence: 91%. Note covers repair review, coverage determination, rental, and recommended actions.",
        "occurred_at": "2026-06-13T10:03:20Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "note_id": "draft-001",
            "sources_used": 4,
            "word_count": 312,
        },
        "governance_decision_id": "gov-draft-001",
        "governance_outcome": "ALLOW",
        "model_id": "mock-standard",
        "task_type": "draft_note",
        "input_tokens": 2140,
        "output_tokens": 428,
        "latency_ms": 312,
        "evidence_count": 4,
        "confidence": 0.91,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-010",
        "event_type": "human.approval.granted",
        "actor_type": "USER",
        "actor_name": "John Smith",
        "status": "SUCCESS",
        "description": "Adjuster John Smith approved draft note draft-001 after human-in-the-loop review. Note cleared for write-back to ClaimCenter.",
        "occurred_at": "2026-06-13T10:04:10Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "note_id": "draft-001",
            "decision": "APPROVED",
            "checklist_passed": 4,
        },
        "governance_decision_id": "gov-appr-001",
        "governance_outcome": "ALLOW",
        "model_id": None,
        "task_type": "draft_note_approval",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": None,
        "evidence_count": None,
        "confidence": None,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
    {
        "event_id": "evt-011",
        "event_type": "claimcenter.note.written",
        "actor_type": "SYSTEM",
        "actor_name": "Write Controller",
        "status": "SUCCESS",
        "description": "The approved draft note is ready for governed write-back.",
        "occurred_at": "2026-06-13T10:04:12Z",
        "user_id": "usr-john-smith",
        "user_role": "ADJUSTER",
        "session_id": "sess-mock-001",
        "claim_id": _CLAIM_ID,
        "claim_number": _CLAIM_ID,
        "payload": {
            "note_id": "draft-001",
            "claimcenter_ref": "CC-NTE-2026-100245-001",
            "write_status": "COMMITTED",
        },
        "governance_decision_id": "gov-appr-001",
        "governance_outcome": "ALLOW",
        "model_id": None,
        "task_type": "claimcenter_write",
        "input_tokens": None,
        "output_tokens": None,
        "latency_ms": 22,
        "evidence_count": None,
        "confidence": None,
        "policy_set": "mvp_policy_set v1.0",
        "routing_reason": None,
    },
]


# ---------------------------------------------------------------------------
# Mock draft note
# ---------------------------------------------------------------------------

_DRAFT_NOTE_CONTENT = """\
RE: Claim CLM-2026-100245 — ABC Logistics Inc. / Auto Liability

Date of Loss: June 8, 2026
Adjuster: John Smith
Date of Note: June 13, 2026

REPAIR ESTIMATE REVIEW

Reviewed repair estimate submitted by Riverside Auto Body dated June 10, 2026. \
Estimated repair cost is $6,200.00, covering damage to the rear bumper assembly, \
trailer hitch, and rear lighting cluster. Parts total $3,800.00; labor total \
$2,400.00. Estimated repair time is 5–7 business days. Estimate is consistent \
with photographic evidence; no frame damage identified.

COVERAGE DETERMINATION

Collision coverage applies under Commercial Auto Policy #CA-2024-8812, \
Section 4.2 — Physical Damage. Subject to $2,500 deductible. Current net \
insurer exposure is estimated at $3,700.00 ($6,200.00 estimate less $2,500.00 \
deductible). Bodily Injury Liability coverage (limit $1,000,000 / deductible \
$5,000) remains open pending receipt of medical records from driver M. Torres.

RENTAL REIMBURSEMENT

Rental reimbursement request for 10 days at $75.00/day ($750.00) remains \
pending approval. Policy provides up to 30 days / $2,250.00 maximum. Rental \
start date is June 9, 2026. Authorization to be confirmed upon receipt of \
signed rental form from insured.

RECOMMENDED ACTIONS

Recommend approval of current repair estimate of $6,200.00 while awaiting \
supplemental inspection upon vehicle teardown. Medical authorization request \
to be sent to M. Torres within 14 days. Third-party insurer to be identified \
and contacted for subrogation evaluation. Reserve maintained at $8,450.00 \
pending final repair invoice and BI determination.
"""

_DRAFT_NOTE = {
    "note_id": "draft-001",
    "claim_id": _CLAIM_ID,
    "generated_at": "2026-06-13T10:15:00Z",
    "content": _DRAFT_NOTE_CONTENT,
    "confidence_score": 0.91,
    "governance_decision": {
        "decision_id": "gov-draft-001",
        "evaluated_at": "2026-06-13T10:15:00Z",
        "task_type": "draft_note",
        "claim_id": _CLAIM_ID,
        "outcome": "ALLOW",
        "reason": (
            "Draft note generation is within policy for task type 'draft_note'. "
            "User role ADJUSTER has 'ai:generate' permission. "
            "Claim risk level MEDIUM does not trigger escalation threshold."
        ),
        "deny_reason": None,
        "escalate_reason": None,
        "policy_evaluations": [
            {
                "policy_id": "base_policy",
                "policy_version": "1.0",
                "rule_id": "require_ai_generate_permission",
                "matched": True,
                "outcome": "ALLOW",
                "reason": "User has 'ai:generate' permission.",
            },
            {
                "policy_id": "draft_note_policy",
                "policy_version": "1.0",
                "rule_id": "allow_draft_for_open_claims",
                "matched": True,
                "outcome": "ALLOW",
                "reason": "Draft note generation is permitted for OPEN claims.",
            },
        ],
        "policy_set_id": "mvp_policy_set",
        "policy_set_version": "1.0",
    },
    "evidence_sources": [
        {
            **_EVIDENCE_SOURCES[1],
            "relevance_score": 0.97,
        },
        {
            **_EVIDENCE_SOURCES[3],
            "relevance_score": 0.93,
        },
        {
            **_EVIDENCE_SOURCES[6],
            "relevance_score": 0.88,
        },
        {
            **_EVIDENCE_SOURCES[5],
            "relevance_score": 0.84,
        },
    ],
    "model_id": "mock-standard",
    "status": "DRAFT",
}

# ---------------------------------------------------------------------------
# Mock approval state (mutable in-memory — resets on server restart)
# ---------------------------------------------------------------------------

_APPROVAL_STATE: dict[str, dict] = {}


def _initial_approval(claim_id: str) -> dict:
    return {
        "approval_id": f"appr-{claim_id}",
        "claim_id": claim_id,
        "draft_note_id": "draft-001",
        "status": "PENDING",          # PENDING | APPROVED | REJECTED | REVISION_REQUESTED
        "reviewer_id": None,
        "reviewer_name": None,
        "decision": None,
        "reviewer_comments": "",
        "decided_at": None,
        "governance_decision": {
            "decision_id": "gov-appr-001",
            "evaluated_at": "2026-06-13T10:15:00Z",
            "task_type": "draft_note_approval",
            "claim_id": claim_id,
            "outcome": "ALLOW",
            "reason": (
                "Approval workflow is within policy. "
                "User role ADJUSTER has 'ai:approve' permission. "
                "Human-in-the-loop review is required before write-back."
            ),
            "deny_reason": None,
            "escalate_reason": None,
            "policy_evaluations": [
                {
                    "policy_id": "base_policy",
                    "policy_version": "1.0",
                    "rule_id": "require_human_approval",
                    "matched": True,
                    "outcome": "ALLOW",
                    "reason": "Human approval is required before any AI-generated note is written to ClaimCenter.",
                },
                {
                    "policy_id": "draft_note_policy",
                    "policy_version": "1.0",
                    "rule_id": "allow_adjuster_approval",
                    "matched": True,
                    "outcome": "ALLOW",
                    "reason": "User role ADJUSTER is authorized to approve draft notes for MEDIUM risk claims.",
                },
            ],
            "policy_set_id": "mvp_policy_set",
            "policy_set_version": "1.0",
        },
        "draft_note": _DRAFT_NOTE,
        "checklist": [
            {"item": "Grounded in evidence", "passed": True, "detail": "All statements cite authorized claim evidence."},
            {"item": "Policy compliant", "passed": True, "detail": "Coverage analysis matches Policy #CA-2024-8812."},
            {"item": "No PII leakage", "passed": True, "detail": "No SSN, DOB, or unauthorized personal data detected."},
            {"item": "Human reviewed", "passed": False, "detail": "Pending adjuster review and approval."},
        ],
    }


# ---------------------------------------------------------------------------
# Repository class
# ---------------------------------------------------------------------------

class MockClaimRepository:
    """
    Phase 1 in-memory implementation.
    Returns hardcoded mock data for CLM-2026-100245.

    Replace this class with ClaimCenterRepository in Phase 2.
    The interface (method signatures and return shapes) does not change.
    """

    def list_claims(self) -> list:
        return _CLAIMS_LIST

    def get_claim(self, claim_id: str) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        return _CLAIM_DETAIL

    def get_claim_summary(self, claim_id: str) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        return _CLAIM_SUMMARY

    def get_claim_evidence(self, claim_id: str) -> list | None:
        if claim_id != _CLAIM_ID:
            return None
        return _EVIDENCE_SOURCES

    def get_claim_audit(self, claim_id: str) -> list | None:
        if claim_id != _CLAIM_ID:
            return None
        return _AUDIT_EVENTS

    def get_draft_note(self, claim_id: str) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        return _DRAFT_NOTE

    def get_approval(self, claim_id: str) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        if claim_id not in _APPROVAL_STATE:
            _APPROVAL_STATE[claim_id] = _initial_approval(claim_id)
        return _APPROVAL_STATE[claim_id]

    def submit_approval(
        self,
        claim_id: str,
        decision: str,
        reviewer_comments: str,
        reviewer_id: str,
        reviewer_name: str,
        decided_at: str,
    ) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        if claim_id not in _APPROVAL_STATE:
            _APPROVAL_STATE[claim_id] = _initial_approval(claim_id)
        state = _APPROVAL_STATE[claim_id]
        state["decision"] = decision
        state["status"] = decision         # APPROVED | REJECTED | REVISION_REQUESTED
        state["reviewer_comments"] = reviewer_comments
        state["reviewer_id"] = reviewer_id
        state["reviewer_name"] = reviewer_name
        state["decided_at"] = decided_at
        # Mark checklist item "Human reviewed" as passed on any decision
        for item in state["checklist"]:
            if item["item"] == "Human reviewed":
                item["passed"] = True
                item["detail"] = f"Reviewed by {reviewer_name} on {decided_at[:10]}."
        return state

    def get_conversation(self, claim_id: str) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None
        return {
            "conversation_id": f"conv-{claim_id}",
            "claim_id": claim_id,
            "turns": list(_CONVERSATION_TURNS.get(claim_id, [])),
        }

    def add_conversation_turn(
        self, claim_id: str, user_message: str, session_id: str
    ) -> dict | None:
        if claim_id != _CLAIM_ID:
            return None

        turn_id = f"turn-{uuid.uuid4().hex[:8]}"
        result = _mock_assistant_response(claim_id, user_message, turn_id)

        # Append to in-memory history
        if claim_id not in _CONVERSATION_TURNS:
            _CONVERSATION_TURNS[claim_id] = []
        _CONVERSATION_TURNS[claim_id].append({
            "turn_id": turn_id,
            "user_message": user_message,
            "assistant_message": result["assistant_message"],
            "sources_used": result["sources_used"],
            "governance_decision": result["governance_decision"],
            "confidence_score": result["confidence_score"],
            "refusal_reason": result["refusal_reason"],
        })
        return result


# ---------------------------------------------------------------------------
# Conversation mock state (per-session in-memory store)
# ---------------------------------------------------------------------------

_CONVERSATION_TURNS: dict[str, list] = {}


def _gov_allow(turn_id: str) -> dict:
    return {
        "decision_id": f"gov-conv-{turn_id}",
        "evaluated_at": "2026-06-13T10:05:00Z",
        "task_type": "claim_assistant",
        "claim_id": _CLAIM_ID,
        "outcome": "ALLOW",
        "reason": (
            "Request is within scope of claim CLM-2026-100245. "
            "User role ADJUSTER has 'ai:generate' permission. "
            "Query is grounded in authorized claim evidence."
        ),
        "deny_reason": None,
        "escalate_reason": None,
        "policy_evaluations": [
            {
                "policy_id": "base_policy",
                "policy_version": "1.0",
                "rule_id": "require_ai_generate_permission",
                "matched": True,
                "outcome": "ALLOW",
                "reason": "User has 'ai:generate' permission.",
            },
            {
                "policy_id": "assistant_scope_policy",
                "policy_version": "1.0",
                "rule_id": "claim_scoped_query",
                "matched": True,
                "outcome": "ALLOW",
                "reason": "Query matches authorized claim evidence for CLM-2026-100245.",
            },
        ],
        "policy_set_id": "mvp_policy_set",
        "policy_set_version": "1.0",
    }


def _gov_deny(turn_id: str) -> dict:
    return {
        "decision_id": f"gov-conv-{turn_id}",
        "evaluated_at": "2026-06-13T10:05:00Z",
        "task_type": "claim_assistant",
        "claim_id": _CLAIM_ID,
        "outcome": "DENY",
        "reason": (
            "Query is outside the authorized scope for claim CLM-2026-100245. "
            "Only questions answerable from authorized claim evidence are permitted."
        ),
        "deny_reason": "OUT_OF_SCOPE",
        "escalate_reason": None,
        "policy_evaluations": [
            {
                "policy_id": "assistant_scope_policy",
                "policy_version": "1.0",
                "rule_id": "claim_scoped_query",
                "matched": True,
                "outcome": "DENY",
                "reason": "Query cannot be answered from authorized claim evidence.",
            },
        ],
        "policy_set_id": "mvp_policy_set",
        "policy_set_version": "1.0",
    }


# ---------------------------------------------------------------------------
# Intent classifier — swap this function to plug in an LLM/embedding later.
# Returns one of the named intent strings; never raises.
# ---------------------------------------------------------------------------

# Each entry is (intent_name, [keyword, ...]).
# Checked top-to-bottom; first match wins.
# Keywords are matched as substrings of the lower-cased, stripped message.
_INTENT_RULES: list[tuple[str, list[str]]] = [
    ("police_report",     ["police report", "police", "incident report", "officer on scene",
                           "fl statute", "citation", "cited for", "summarize the police",
                           "what does the police"]),
    ("repair_estimate",   ["repair estimate", "damage estimate", "repair cost", "body shop",
                           "how much is the", "how much does", "how much will",
                           "what is the repair", "what is the damage", "what is the estimate",
                           "cost of repair", "cost of damage", "repair bill",
                           "riverside", "estimate", "repair"]),
    ("total_loss",        ["total loss", "loss threshold", "loss amount", "totaled"]),
    ("coverage",          ["coverage", "what coverage", "covered", "deductible",
                           "policy section", "policy limit", "bodily injury",
                           "collision", "rental reimbursement", "what does the policy"]),
    ("outstanding_issues",["outstanding", "open issue", "pending issue", "remaining issue",
                           "what issue", "what are the issue", "unresolved",
                           "what still need", "what needs to"]),
    ("claim_summary",     ["summarize the claim", "claim summary", "what happened",
                           "overview of the claim", "give me a summary", "summarize this"]),
    ("rental",            ["rental", "rent-a-car", "enterprise rent", "rental extension",
                           "rental request", "rental approval", "rental period"]),
    ("draft_note",        ["draft", "write a note", "write a claim note", "document this"]),
]


def _classify_intent(message: str) -> str:
    """
    Deterministic keyword classifier.  Returns an intent name or 'out_of_scope'.
    Replace the body of this function to plug in embeddings or an LLM router.
    """
    msg = message.lower().strip()
    for intent, keywords in _INTENT_RULES:
        if any(kw in msg for kw in keywords):
            return intent
    return "out_of_scope"


def _mock_assistant_response(claim_id: str, user_message: str, turn_id: str) -> dict:
    intent = _classify_intent(user_message)

    # ── police_report ───────────────────────────────────────────────────────
    if intent == "police_report":
        return {
            "assistant_message": (
                "Based on Police Report #MIA-2026-88421 for CLM-2026-100245:\n\n"
                "- **At-fault determination** — Officer on scene confirmed a rear-end "
                "collision. The third-party driver was cited for failure to maintain safe "
                "following distance (FL Statute 316.0895). No DUI involvement.\n\n"
                "- **Parties** — All parties were ambulatory at the scene. Driver M. Torres "
                "reported neck stiffness but declined ambulance transport.\n\n"
                "- **Vehicle** — Insured vehicle (2023 Freightliner Cascadia, plate FL-LGT-8821) "
                "was stationary at a red light at I-75 & Exit 42, Miami, FL at time of impact.\n\n"
                "The police report establishes clear third-party liability and supports "
                "subrogation recovery against the at-fault driver."
            ),
            "sources_used": [_EVIDENCE_SOURCES[0], _EVIDENCE_SOURCES[2]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.98,
            "refusal_reason": None,
        }

    # ── repair_estimate ─────────────────────────────────────────────────────
    if intent == "repair_estimate":
        return {
            "assistant_message": (
                "Based on the repair estimate submitted by Riverside Auto Body:\n\n"
                "- **Total repair estimate: $6,200.00**\n"
                "  - Parts: $3,800.00 (rear bumper assembly, trailer hitch, rear lighting cluster)\n"
                "  - Labor: $2,400.00\n"
                "  - Estimated repair time: 5–7 business days\n\n"
                "- **Net insurer exposure** — After the $2,500 Physical Damage deductible, "
                "the insurer's share is **$3,700.00**.\n\n"
                "- **Photo consistency** — The estimate is consistent with photographic "
                "evidence. No frame damage was visible in the submitted photos.\n\n"
                "A final supplement has not yet been received. The reserve of $8,450 includes "
                "estimated rental reimbursement and a contingency buffer above the current estimate."
            ),
            "sources_used": [_EVIDENCE_SOURCES[1], _EVIDENCE_SOURCES[4]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.96,
            "refusal_reason": None,
        }

    # ── total_loss ──────────────────────────────────────────────────────────
    if intent == "total_loss":
        return {
            "assistant_message": (
                "Based on the claim file for CLM-2026-100245:\n\n"
                "- **Current repair estimate: $6,200.00** — submitted by Riverside Auto Body.\n\n"
                "- **Total loss threshold** — Commercial Auto Policy #CA-2024-8812 does not "
                "specify a fixed percentage threshold; determination would be made by an "
                "appraiser if repair costs approach the vehicle's Actual Cash Value (ACV).\n\n"
                "- **Current assessment** — No frame damage was identified in submitted photos. "
                "The 2023 Freightliner Cascadia has an estimated ACV well above the current "
                "repair estimate. Total loss risk is **low** at this time.\n\n"
                "The reserve of $8,450 may require upward adjustment if a repair supplement "
                "is received or if BI exposure develops."
            ),
            "sources_used": [_EVIDENCE_SOURCES[1], _EVIDENCE_SOURCES[4], _EVIDENCE_SOURCES[3]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.93,
            "refusal_reason": None,
        }

    # ── coverage ────────────────────────────────────────────────────────────
    if intent == "coverage":
        return {
            "assistant_message": (
                "The following coverages apply to claim CLM-2026-100245 under "
                "Commercial Auto Policy #CA-2024-8812:\n\n"
                "- **Bodily Injury Liability** — Limit: $1,000,000 per occurrence | "
                "Deductible: $5,000. Applies to any third-party injury claims arising "
                "from this incident (Policy Section 4.2). BI exposure is possible given "
                "the driver's reported neck stiffness.\n\n"
                "- **Physical Damage – Collision** — Limit: $250,000 | Deductible: $2,500. "
                "Applies to the $6,200 repair estimate. Net insurer exposure after deductible: $3,700.\n\n"
                "- **Rental Reimbursement** — $75/day up to 30 days (max $2,250). "
                "Estimated usage: 10 days ($750). Rental authorization is pending."
            ),
            "sources_used": [_EVIDENCE_SOURCES[3], _EVIDENCE_SOURCES[5], _EVIDENCE_SOURCES[6]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.97,
            "refusal_reason": None,
        }

    # ── outstanding_issues ──────────────────────────────────────────────────
    if intent == "outstanding_issues":
        return {
            "assistant_message": (
                "Based on the authorized claim evidence for CLM-2026-100245, "
                "the following issues remain outstanding:\n\n"
                "1. **Awaiting repair supplement from body shop** — "
                "Riverside Auto Body has not yet submitted a final supplement. "
                "The current estimate of $6,200 may change upon vehicle teardown.\n\n"
                "2. **Rental extension request pending approval** — "
                "M. Torres submitted a rental authorization for 10 days ($750). "
                "No approval or denial has been recorded in the claim file.\n\n"
                "3. **Confirm no-injury status** — "
                "Driver reported neck stiffness and sought independent medical care. "
                "Medical records have not been received. Bodily injury exposure "
                "cannot be confirmed or closed until records are obtained."
            ),
            "sources_used": [_EVIDENCE_SOURCES[1], _EVIDENCE_SOURCES[2], _EVIDENCE_SOURCES[6]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.92,
            "refusal_reason": None,
        }

    # ── claim_summary ───────────────────────────────────────────────────────
    if intent == "claim_summary":
        return {
            "assistant_message": (
                "**Summary of CLM-2026-100245:**\n\n"
                "On June 8, 2026, a 2023 Freightliner Cascadia operated by ABC Logistics Inc. "
                "was struck from behind while stationary at a red light at I-75 & Exit 42, "
                "Miami, FL. The at-fault third party was cited by police (FL Statute 316.0895). "
                "Driver M. Torres reported neck stiffness and sought independent medical evaluation.\n\n"
                "The vehicle sustained rear bumper and lighting damage estimated at $6,200. "
                "Coverage under Commercial Auto Policy #CA-2024-8812 is confirmed active. "
                "The current reserve is $8,450. BI exposure and subrogation recovery are pending."
            ),
            "sources_used": [_EVIDENCE_SOURCES[0], _EVIDENCE_SOURCES[1], _EVIDENCE_SOURCES[3]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.94,
            "refusal_reason": None,
        }

    # ── rental ──────────────────────────────────────────────────────────────
    if intent == "rental":
        return {
            "assistant_message": (
                "Based on the rental authorization on file for CLM-2026-100245:\n\n"
                "- **Rental requested by** M. Torres (driver) for business operations continuity.\n"
                "- **Policy provides** $75/day up to 30 days (maximum $2,250).\n"
                "- **Rental start date:** 2026-06-09.\n"
                "- **Estimated rental period:** 10 days ($750 estimated cost).\n"
                "- **Status:** Rental extension request is **pending approval**. "
                "No approval or denial has been recorded in the claim file.\n\n"
                "Rental should be closed upon vehicle return from Riverside Auto Body "
                "and reconciled against the policy limit."
            ),
            "sources_used": [_EVIDENCE_SOURCES[6], _EVIDENCE_SOURCES[5]],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 0.95,
            "refusal_reason": None,
        }

    # ── draft_note ──────────────────────────────────────────────────────────
    if intent == "draft_note":
        return {
            "assistant_message": (
                "Draft Note generation is available as a separate governed workflow. "
                "Please navigate to the **Draft Note** tab to initiate an AI-assisted "
                "note for this claim. The draft will be reviewed and approved before "
                "any write-back to ClaimCenter."
            ),
            "sources_used": [],
            "governance_decision": _gov_allow(turn_id),
            "confidence_score": 1.0,
            "refusal_reason": None,
        }

    # ── out_of_scope refusal ────────────────────────────────────────────────
    return {
        "assistant_message": (
            "This assistant is scoped to claim CLM-2026-100245 and can only answer "
            "using authorized claim evidence. Your question cannot be answered from "
            "the available claim documents, policy records, or adjuster notes for this claim.\n\n"
            "Try asking about outstanding issues, coverage, repair estimates, or "
            "other topics directly related to this claim."
        ),
        "sources_used": [],
        "governance_decision": _gov_deny(turn_id),
        "confidence_score": 0.0,
        "refusal_reason": (
            "OUT_OF_SCOPE: Query cannot be answered from authorized claim evidence "
            "for CLM-2026-100245."
        ),
    }
