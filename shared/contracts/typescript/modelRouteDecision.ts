// ModelRouteDecision contract
// Represents the model router's selection decision for a given task.
// Attached to every AI response so the adjuster can see which model handled it.

export enum TaskType {
  ClaimSummary = "claim_summary",
  ClaimQa = "claim_qa",
  DraftNote = "draft_note",
  GovernanceCheck = "governance_check",
  AuditExplanation = "audit_explanation",
  HighRiskEscalation = "high_risk_escalation",
}

export enum ModelTier {
  Standard = "STANDARD",
  Premium = "PREMIUM",
  Mock = "MOCK",
}

export enum RoutingReason {
  TaskTypeDefault = "TASK_TYPE_DEFAULT",
  HighRiskClaim = "HIGH_RISK_CLAIM",
  LowConfidenceReroute = "LOW_CONFIDENCE_REROUTE",
  ProviderFailover = "PROVIDER_FAILOVER",
  CostThresholdOverride = "COST_THRESHOLD_OVERRIDE",
}

export interface ModelRouteDecision {
  routeId: string;
  decidedAt: string;         // ISO 8601
  taskType: TaskType;

  // Selected model
  modelId: string;           // e.g. "claude-sonnet-4-6", "mock-standard"
  modelTier: ModelTier;
  providerId: string;        // e.g. "anthropic", "azure_openai", "mock"

  // Why this model was chosen
  routingReason: RoutingReason;
  routingRationale: string;  // human-readable explanation

  // Routing inputs
  claimRiskLevel: string | null;
  estimatedCost: number | null;   // USD, estimated before call
  actualCost: number | null;      // USD, populated after call

  // Fallback — populated if primary provider was unavailable
  primaryModelId: string | null;
  fallbackReason: string | null;
}
