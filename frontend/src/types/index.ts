// Frontend types matching backend API snake_case responses.
// These mirror shared/contracts/typescript but use snake_case to match
// the Python dict responses returned by the FastAPI backend.

// ── Enums ──────────────────────────────────────────────────────────────────

export type ClaimStatus = 'OPEN' | 'IN_REVIEW' | 'PENDING' | 'CLOSED' | 'DENIED'
export type ClaimType =
  | 'AUTO_LIABILITY'
  | 'AUTO_PHYSICAL_DAMAGE'
  | 'PROPERTY_DAMAGE'
  | 'WORKERS_COMPENSATION'
  | 'GENERAL_LIABILITY'
  | 'MEDICAL_MALPRACTICE'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type GovernanceOutcome = 'ALLOW' | 'DENY' | 'ESCALATE'
export type ModelTier = 'STANDARD' | 'PREMIUM' | 'MOCK'
export type SourceType =
  | 'CLAIM_DOCUMENT'
  | 'KNOWLEDGE_BASE'
  | 'CLAIM_NOTE'
  | 'POLICY_DOCUMENT'
  | 'REGULATION'

// ── Session ────────────────────────────────────────────────────────────────

export interface MockUser {
  user_id: string
  name: string
  email: string
  role: string
  permissions: string[]
}

export interface Session {
  session_id: string
  user: MockUser
  identity_provider: string
  expires_at: string
}

// ── Claims ─────────────────────────────────────────────────────────────────

export interface ClaimListItem {
  claim_id: string
  claim_number: string
  status: ClaimStatus
  type: ClaimType
  risk_level: RiskLevel
  date_of_loss: string
  reserve_amount: number
  primary_insured_name: string
}

export interface ClaimParty {
  party_id: string
  role: string
  name: string
  contact_phone: string | null
  contact_email: string | null
  represented_by: string | null
}

export interface Coverage {
  coverage_id: string
  coverage_type: string
  limit: number
  deductible: number
  is_applicable: boolean
}

export interface ClaimDocument {
  document_id: string
  title: string
  document_type: string
  uploaded_at: string
  uploaded_by: string
}

export interface ClaimNote {
  note_id: string
  content: string
  author: string
  authored_at: string
  is_ai_generated: boolean
  approved_by: string | null
  approved_at: string | null
}

export interface Claim {
  claim_id: string
  claim_number: string
  status: ClaimStatus
  type: ClaimType
  risk_level: RiskLevel
  date_of_loss: string
  reported_at: string
  description: string
  reserve_amount: number
  paid_amount: number
  litigation_flag: boolean
  jurisdiction_code: string
  parties: ClaimParty[]
  coverages: Coverage[]
  notes: ClaimNote[]
  documents: ClaimDocument[]
}

// ── Evidence ───────────────────────────────────────────────────────────────

export interface EvidenceSource {
  source_id: string
  source_type: SourceType
  title: string
  excerpt: string
  relevance_score: number
  document_id: string | null
  page_reference: string | null
  retrieved_at: string
}

// ── Governance ─────────────────────────────────────────────────────────────

export interface PolicyEvaluation {
  policy_id: string
  policy_version: string
  rule_id: string
  matched: boolean
  outcome: GovernanceOutcome
  reason: string
}

export interface GovernanceDecision {
  decision_id: string
  evaluated_at: string
  task_type: string
  claim_id: string | null
  outcome: GovernanceOutcome
  reason: string
  deny_reason: string | null
  escalate_reason: string | null
  policy_evaluations: PolicyEvaluation[]
  policy_set_id: string
  policy_set_version: string
}

// ── Model Routing ──────────────────────────────────────────────────────────

export interface ModelRouteDecision {
  route_id: string
  decided_at: string
  task_type: string
  model_id: string
  model_tier: ModelTier
  provider_id: string
  routing_reason: string
  routing_rationale: string
  claim_risk_level: string | null
  estimated_cost: number | null
  actual_cost: number | null
  primary_model_id: string | null
  fallback_reason: string | null
}

// ── Claim Summary ──────────────────────────────────────────────────────────

export interface ClaimSummary {
  summary_id: string
  claim_id: string
  generated_at: string
  summary: string
  coverage_analysis: string
  key_findings: string[]
  open_issues: string[]
  recommended_actions: string[]
  risk_indicators: string[]
  evidence_score: number
  confidence_score: number
  confidence_rationale: string
  sources_used: number
  evidence_sources: EvidenceSource[]
  governance_decision: GovernanceDecision
  model_route_decision: ModelRouteDecision
}

// ── Approval ───────────────────────────────────────────────────────────────

export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED'

export interface ChecklistItem {
  item: string
  passed: boolean
  detail: string
}

export interface ApprovalRecord {
  approval_id: string
  claim_id: string
  draft_note_id: string
  status: ApprovalStatus
  reviewer_id: string | null
  reviewer_name: string | null
  decision: string | null
  reviewer_comments: string
  decided_at: string | null
  governance_decision: GovernanceDecision
  draft_note: DraftNote
  checklist: ChecklistItem[]
}

export interface ApprovalRequest {
  decision: 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED'
  reviewer_comments: string
  reviewer_id?: string
  reviewer_name?: string
}

// ── Draft Note ─────────────────────────────────────────────────────────────

export type DraftNoteStatus = 'DRAFT' | 'APPROVED' | 'REJECTED' | 'WRITTEN'

export interface DraftNote {
  note_id: string
  claim_id: string
  generated_at: string
  content: string
  confidence_score: number
  governance_decision: GovernanceDecision
  evidence_sources: EvidenceSource[]
  model_id: string
  status: DraftNoteStatus
}

// ── Conversation ───────────────────────────────────────────────────────────

export interface ConversationTurn {
  turn_id: string
  user_message: string
  assistant_message: string
  sources_used: EvidenceSource[]
  governance_decision: GovernanceDecision
  confidence_score: number
  refusal_reason: string | null
}

export interface Conversation {
  conversation_id: string
  claim_id: string
  turns: ConversationTurn[]
}

export interface ConversationTurnResponse {
  turn_id: string
  user_message?: string
  assistant_message: string
  sources_used: EvidenceSource[]
  governance_decision: GovernanceDecision
  confidence_score: number
  refusal_reason: string | null
}

// ── Audit ──────────────────────────────────────────────────────────────────

export type AuditActorType = 'USER' | 'AI' | 'GOVERNANCE' | 'SYSTEM'
export type AuditEventStatus = 'INFO' | 'SUCCESS' | 'ALLOW' | 'DENY' | 'ESCALATE'

export interface AuditEvent {
  event_id: string
  event_type: string
  occurred_at: string
  user_id: string
  user_role: string
  session_id: string
  claim_id: string | null
  claim_number: string | null
  payload: Record<string, unknown>
  governance_decision_id: string | null
  governance_outcome: GovernanceOutcome | null
  model_id: string | null
  task_type: string | null
  input_tokens: number | null
  output_tokens: number | null
  latency_ms: number | null
  // Extended fields (Step 7)
  actor_type: AuditActorType | null
  actor_name: string | null
  status: AuditEventStatus | null
  description: string | null
  evidence_count: number | null
  confidence: number | null
  policy_set: string | null
  routing_reason: string | null
}
