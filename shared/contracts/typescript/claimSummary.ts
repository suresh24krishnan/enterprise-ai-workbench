// ClaimSummary contract
// Represents the governed AI-generated summary of a claim.

import type { EvidenceSource } from "./evidenceSource";
import type { GovernanceDecision } from "./governanceDecision";
import type { ModelRouteDecision } from "./modelRouteDecision";

export interface ClaimSummary {
  summaryId: string;
  claimId: string;
  generatedAt: string;         // ISO 8601

  // Core AI output
  summary: string;
  keyFindings: string[];       // Bullet-point findings extracted by the model
  coverageAnalysis: string;    // Which coverages apply and why
  recommendedActions: string[]; // Next steps the adjuster should consider

  // Grounding and provenance
  evidenceSources: EvidenceSource[];

  // Governance and routing metadata
  governanceDecision: GovernanceDecision;
  modelRouteDecision: ModelRouteDecision;

  // Confidence
  confidenceScore: number;     // 0.0 – 1.0
  confidenceRationale: string;
}
