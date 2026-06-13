// DraftClaimNote contract
// Represents an AI-generated note draft awaiting human review and approval.

import type { EvidenceSource } from "./evidenceSource";
import type { GovernanceDecision } from "./governanceDecision";
import type { ModelRouteDecision } from "./modelRouteDecision";

export enum DraftNoteStatus {
  PendingReview = "PENDING_REVIEW",   // Awaiting human review
  Approved = "APPROVED",              // Human approved — ready to write
  Rejected = "REJECTED",              // Human rejected — draft discarded
  Written = "WRITTEN",                // Successfully written to ClaimCenter
  WriteFailed = "WRITE_FAILED",       // Write attempted but failed
}

export enum NoteCategory {
  ProgressNote = "PROGRESS_NOTE",
  CoverageAnalysis = "COVERAGE_ANALYSIS",
  LiabilityAssessment = "LIABILITY_ASSESSMENT",
  ReserveJustification = "RESERVE_JUSTIFICATION",
  ClosingNote = "CLOSING_NOTE",
  EscalationNote = "ESCALATION_NOTE",
}

export interface DraftClaimNote {
  draftId: string;
  claimId: string;
  conversationId: string | null;  // originating conversation, if applicable
  status: DraftNoteStatus;
  category: NoteCategory;
  createdAt: string;              // ISO 8601
  updatedAt: string;

  // AI-generated content
  aiContent: string;

  // Human-edited content (starts as copy of aiContent, user may edit before approving)
  editedContent: string;

  // Grounding
  evidenceSources: EvidenceSource[];

  // Governance — always ESCALATE for draft_note task type
  governanceDecision: GovernanceDecision;
  modelRouteDecision: ModelRouteDecision;

  // Human decision
  reviewedBy: string | null;
  reviewedAt: string | null;      // ISO 8601
  reviewerComments: string | null;

  // Write outcome (populated after status = WRITTEN or WRITE_FAILED)
  claimCenterNoteId: string | null;
  writeAttemptedAt: string | null;
  writeFailureReason: string | null;
}
