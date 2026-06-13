// AuditEvent contract
// Represents an immutable audit record. Once written, never modified.

import type { GovernanceOutcome } from "./governanceDecision";

export enum AuditEventType {
  // Session
  UserLogin = "user.login",
  UserLogout = "user.logout",
  SessionExpired = "user.session_expired",

  // Claims
  ClaimSelected = "claim.selected",
  ClaimSearched = "claim.searched",

  // AI — reads
  SummaryGenerated = "ai.summary.generated",
  ConversationTurnCompleted = "ai.conversation.turn_completed",
  KnowledgeRetrieved = "ai.rag.retrieved",

  // AI — writes
  NoteDrafted = "ai.note.drafted",

  // Governance
  GovernanceEvaluated = "governance.evaluated",

  // Human decisions
  HumanApprovalRequested = "human.approval.requested",
  HumanApprovalGranted = "human.approval.granted",
  HumanApprovalRejected = "human.approval.rejected",

  // Writes to external systems
  ClaimNoteWritten = "claimcenter.note.written",
  ClaimNoteWriteFailed = "claimcenter.note.write_failed",
}

export interface AuditEvent {
  eventId: string;               // UUID, assigned by audit store
  eventType: AuditEventType;
  occurredAt: string;            // ISO 8601 UTC

  // Who and where
  userId: string;
  userRole: string;
  sessionId: string;

  // What claim (if applicable)
  claimId: string | null;
  claimNumber: string | null;

  // Event-specific payload (varies by eventType)
  payload: Record<string, unknown>;

  // Governance context (if a governance decision was involved)
  governanceDecisionId: string | null;
  governanceOutcome: GovernanceOutcome | null;

  // Model context (if an AI model was called)
  modelId: string | null;
  taskType: string | null;
  inputTokens: number | null;
  outputTokens: number | null;
  latencyMs: number | null;
}
