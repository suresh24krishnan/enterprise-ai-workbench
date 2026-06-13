// ConversationTurn contract
// Represents a single user/assistant exchange within a scoped claim conversation.

import type { EvidenceSource } from "./evidenceSource";
import type { GovernanceDecision } from "./governanceDecision";
import type { ModelRouteDecision } from "./modelRouteDecision";

export enum TurnRole {
  User = "USER",
  Assistant = "ASSISTANT",
  System = "SYSTEM", // governance denial or escalation notice
}

export enum TurnStatus {
  Completed = "COMPLETED",
  Denied = "DENIED",           // governance denied the request
  PendingApproval = "PENDING_APPROVAL", // escalated, awaiting human
  Approved = "APPROVED",
  Rejected = "REJECTED",
}

export interface ConversationTurn {
  turnId: string;
  conversationId: string;
  claimId: string;
  sequenceNumber: number;      // 1-based, monotonically increasing
  role: TurnRole;
  status: TurnStatus;
  createdAt: string;           // ISO 8601

  // User input
  userMessage: string;

  // AI output (null if denied or pending)
  assistantMessage: string | null;

  // Grounding
  evidenceSources: EvidenceSource[];

  // Governance and routing (populated when role = ASSISTANT)
  governanceDecision: GovernanceDecision | null;
  modelRouteDecision: ModelRouteDecision | null;

  // Audit
  auditEventId: string | null;
}

export interface Conversation {
  conversationId: string;
  claimId: string;
  userId: string;
  status: "ACTIVE" | "CLOSED" | "PENDING_APPROVAL";
  startedAt: string;           // ISO 8601
  updatedAt: string;
  turns: ConversationTurn[];
}
