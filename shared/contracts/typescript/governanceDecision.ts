// GovernanceDecision contract
// Represents the outcome of evaluating a request against governance policy.
// Every AI action produces exactly one GovernanceDecision before proceeding.

export enum GovernanceOutcome {
  Allow = "ALLOW",
  Deny = "DENY",
  Escalate = "ESCALATE",
}

export enum GovernanceDenyReason {
  PolicyViolation = "POLICY_VIOLATION",
  InsufficientPermission = "INSUFFICIENT_PERMISSION",
  OutOfScope = "OUT_OF_SCOPE",
  PiiExposureRisk = "PII_EXPOSURE_RISK",
  HighRiskActionBlocked = "HIGH_RISK_ACTION_BLOCKED",
}

export enum GovernanceEscalateReason {
  HumanApprovalRequired = "HUMAN_APPROVAL_REQUIRED",
  HighReserveAmount = "HIGH_RESERVE_AMOUNT",
  LitigationFlag = "LITIGATION_FLAG",
  LowModelConfidence = "LOW_MODEL_CONFIDENCE",
  SensitiveContentDetected = "SENSITIVE_CONTENT_DETECTED",
}

export interface PolicyEvaluation {
  policyId: string;
  policyVersion: string;
  ruleId: string;
  matched: boolean;
  outcome: GovernanceOutcome;
  reason: string;
}

export interface GovernanceDecision {
  decisionId: string;
  evaluatedAt: string;             // ISO 8601
  taskType: string;                // e.g. "claim_summary", "draft_note"
  claimId: string | null;

  // Final outcome — strictest rule wins (DENY > ESCALATE > ALLOW)
  outcome: GovernanceOutcome;

  // Human-readable explanation always present
  reason: string;

  // Populated when outcome = DENY
  denyReason: GovernanceDenyReason | null;

  // Populated when outcome = ESCALATE
  escalateReason: GovernanceEscalateReason | null;

  // Individual policy evaluations that led to this decision
  policyEvaluations: PolicyEvaluation[];

  // Which policy set was active
  policySetId: string;
  policySetVersion: string;
}
