"""
Planner — maps intent to required providers.

DETERMINISTIC: for a given ClaimIntent, the same provider list is always
returned. There is no runtime adaptation, no ML, and no randomness.

The plan is a static lookup. Adding a new intent requires adding an entry
to _INTENT_PROVIDER_MAP and redeploying — there is no dynamic re-planning.

Intent → provider selection rationale:

  claim_summary      — full cross-system picture: claim, policy, customer
                       history, fraud risk, recent correspondence.
                       Uses 5 providers.

  coverage_analysis  — which coverages apply: claim details + policy.
                       Uses 2 providers.

  fraud_check        — fraud indicators + claim details for context.
                       Uses 2 providers.

  document_review    — all documents attached to the claim.
                       Uses 1 provider.

  policy_lookup      — policy and customer profile only.
                       Uses 2 providers.
"""

from __future__ import annotations

from .models import ClaimIntent

# ---------------------------------------------------------------------------
# Static intent → provider plan
# ---------------------------------------------------------------------------

_INTENT_PROVIDER_MAP: dict[ClaimIntent, list[str]] = {
    ClaimIntent.CLAIM_SUMMARY: [
        "claimcenter",
        "policycenter",
        "edw",
        "fraud",
        "email",
    ],
    ClaimIntent.COVERAGE_ANALYSIS: [
        "claimcenter",
        "policycenter",
    ],
    ClaimIntent.FRAUD_CHECK: [
        "claimcenter",
        "fraud",
    ],
    ClaimIntent.DOCUMENT_REVIEW: [
        "documents",
    ],
    ClaimIntent.POLICY_LOOKUP: [
        "policycenter",
        "edw",
    ],
}

# ---------------------------------------------------------------------------
# Rule-based intent classifier
# ---------------------------------------------------------------------------

_KEYWORD_MAP: list[tuple[list[str], ClaimIntent]] = [
    (["fraud", "siu", "suspicious", "indicator"],    ClaimIntent.FRAUD_CHECK),
    (["document", "attachment", "file", "evidence"], ClaimIntent.DOCUMENT_REVIEW),
    (["coverage", "policy limit", "deductible"],     ClaimIntent.COVERAGE_ANALYSIS),
    (["policy", "policyholder", "insured"],          ClaimIntent.POLICY_LOOKUP),
    (["summary", "overview", "full", "claim"],       ClaimIntent.CLAIM_SUMMARY),
]


def classify_intent(raw_intent: str) -> ClaimIntent:
    """
    Map a raw intent string to a ClaimIntent enum value.

    Matching order:
    1. Exact enum value match (e.g. "fraud_check")
    2. Keyword scan (first match wins, ordered by specificity)
    3. Default: CLAIM_SUMMARY

    This is rule-based, not ML. For a given input, the output is always
    the same — no probabilistic or session-dependent behaviour.
    """
    normalised = raw_intent.strip().lower().replace("-", "_").replace(" ", "_")

    # Exact match against enum values
    try:
        return ClaimIntent(normalised)
    except ValueError:
        pass

    # Keyword scan on the original (un-normalised) string
    lower = raw_intent.lower()
    for keywords, intent in _KEYWORD_MAP:
        if any(kw in lower for kw in keywords):
            return intent

    return ClaimIntent.CLAIM_SUMMARY


def build_plan(intent: ClaimIntent) -> list[str]:
    """Return the ordered list of provider names for a given intent."""
    return list(_INTENT_PROVIDER_MAP[intent])
