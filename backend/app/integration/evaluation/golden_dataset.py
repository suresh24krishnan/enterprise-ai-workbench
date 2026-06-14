"""
Golden dataset — 10 deterministic evaluation scenarios.

Every scenario is fully deterministic: claim_id, intent, and all expectations
are fixed constants. No LLM outputs, no prompt text, no randomness.

Claim ID selection:
  CLM-2026-100245 — the single claim known to all 5 mock providers.
                    Required for any scenario involving claimcenter, fraud,
                    email, or documents, which only return success for this ID.
  CLM-EVAL-0005   — policycenter and edw return success for any claim ID,
                    so GS-005 (policy_lookup) can use a distinct evaluation claim.

Adding a new scenario: append to GOLDEN_SCENARIOS and increment the version.
"""

from __future__ import annotations

from backend.app.integration.evaluation.models import GoldenExpectation, GoldenScenario

DATASET_VERSION = "1.0"

# CLM-2026-100245 is the only claim in all 5 mock provider datasets.
_FULL_CLAIM = "CLM-2026-100245"

# policycenter and edw return success for any claim ID.
_POLICY_CLAIM = "CLM-EVAL-0005"

# ── Scenarios ──────────────────────────────────────────────────────────────

GOLDEN_SCENARIOS: list[GoldenScenario] = [

    # 1 — Full claim summary: all 5 providers
    GoldenScenario(
        scenario_id="GS-001",
        name="Claim Summary — Full Provider Set",
        description="Full claim summary triggers all 5 providers in order.",
        claim_id=_FULL_CLAIM,
        intent="claim_summary",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
            expected_provider_count=5,
            expected_success_count=5,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["smoke", "full-provider"],
    ),

    # 2 — Coverage analysis: ClaimCenter + PolicyCenter
    GoldenScenario(
        scenario_id="GS-002",
        name="Coverage Analysis — ClaimCenter + PolicyCenter",
        description="Coverage lookup requires ClaimCenter and PolicyCenter only.",
        claim_id=_FULL_CLAIM,
        intent="coverage_analysis",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter"],
            expected_provider_count=2,
            expected_success_count=2,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["coverage"],
    ),

    # 3 — Fraud check: ClaimCenter + Fraud
    GoldenScenario(
        scenario_id="GS-003",
        name="Fraud Review — ClaimCenter + Fraud Engine",
        description="Fraud check routes to ClaimCenter and Fraud provider.",
        claim_id=_FULL_CLAIM,
        intent="fraud_check",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "fraud"],
            expected_provider_count=2,
            expected_success_count=2,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["fraud"],
    ),

    # 4 — Document review: Documents provider only
    GoldenScenario(
        scenario_id="GS-004",
        name="Document Search — Documents Provider",
        description="Document review routes exclusively to the documents provider.",
        claim_id=_FULL_CLAIM,
        intent="document_review",
        expectation=GoldenExpectation(
            expected_providers=["documents"],
            expected_provider_count=1,
            expected_success_count=1,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["documents"],
    ),

    # 5 — Policy lookup: PolicyCenter + EDW
    # policycenter and edw return success for any claim ID — uses a distinct eval claim.
    GoldenScenario(
        scenario_id="GS-005",
        name="Policy Lookup — PolicyCenter + EDW",
        description="Policy lookup retrieves from PolicyCenter and EDW. Both succeed for any claim.",
        claim_id=_POLICY_CLAIM,
        intent="policy_lookup",
        expectation=GoldenExpectation(
            expected_providers=["policycenter", "edw"],
            expected_provider_count=2,
            expected_success_count=2,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["policy"],
    ),

    # 6 — Customer profile: full claim summary verifying EDW customer data
    GoldenScenario(
        scenario_id="GS-006",
        name="Customer Profile — Full Claim Summary",
        description="Verifies EDW (customer profile) is always included in claim_summary.",
        claim_id=_FULL_CLAIM,
        intent="claim_summary",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
            expected_provider_count=5,
            expected_success_count=5,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["customer-profile", "full-provider"],
    ),

    # 7 — Email metadata: verifies email provider is included in claim_summary
    GoldenScenario(
        scenario_id="GS-007",
        name="Email Metadata — Included in Claim Summary",
        description="Email provider is always included in claim_summary intent.",
        claim_id=_FULL_CLAIM,
        intent="claim_summary",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
            expected_provider_count=5,
            expected_success_count=5,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["email-metadata"],
    ),

    # 8 — Reserve review via coverage_analysis path
    GoldenScenario(
        scenario_id="GS-008",
        name="Reserve Review — Coverage Analysis Path",
        description="Reserve review uses coverage_analysis (ClaimCenter + PolicyCenter).",
        claim_id=_FULL_CLAIM,
        intent="coverage_analysis",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter"],
            expected_provider_count=2,
            expected_success_count=2,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["reserve"],
    ),

    # 9 — Timeline review via fraud_check path
    GoldenScenario(
        scenario_id="GS-009",
        name="Timeline Review — Fraud Check Path",
        description="Timeline review uses fraud_check path (ClaimCenter + Fraud).",
        claim_id=_FULL_CLAIM,
        intent="fraud_check",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "fraud"],
            expected_provider_count=2,
            expected_success_count=2,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["timeline"],
    ),

    # 10 — Determinism check: same intent → same 5 providers → same order every time
    GoldenScenario(
        scenario_id="GS-010",
        name="Multi-Provider Claim Summary — Determinism Check",
        description="Verifies same claim_summary intent always selects 5 providers in the same order.",
        claim_id=_FULL_CLAIM,
        intent="claim_summary",
        expectation=GoldenExpectation(
            expected_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
            expected_provider_count=5,
            expected_success_count=5,
            writes_expected=False,
            real_providers_expected=False,
            max_latency_ms=500.0,
            execution_order_strict=True,
        ),
        tags=["determinism", "stress", "full-provider"],
    ),
]

# ── Index ──────────────────────────────────────────────────────────────────

_SCENARIO_INDEX: dict[str, GoldenScenario] = {s.scenario_id: s for s in GOLDEN_SCENARIOS}


def get_scenario(scenario_id: str) -> GoldenScenario | None:
    return _SCENARIO_INDEX.get(scenario_id)


def list_scenarios() -> list[GoldenScenario]:
    return list(GOLDEN_SCENARIOS)


def scenario_count() -> int:
    return len(GOLDEN_SCENARIOS)
