import type {
  ApprovalRecord,
  ApprovalRequest,
  AuditEvent,
  Claim,
  ClaimListItem,
  ClaimSummary,
  Conversation,
  ConversationTurnResponse,
  DraftNote,
  EvidenceSource,
  Session,
} from '@/types'

// Phase 1 local dev: points to port 8005 (permissive CORS, all localhost origins).
// Set VITE_API_BASE_URL to override (e.g. when using the Vite proxy on port 8000).
const BASE: string = (import.meta.env['VITE_API_BASE_URL'] as string | undefined) || 'http://localhost:8006'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText} — ${path}`)
  }
  return res.json() as Promise<T>
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText} — ${path}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  session:          ()                                               => get<Session>('/api/session'),
  claims:           ()                                               => get<ClaimListItem[]>('/api/claims'),
  claim:            (id: string)                                     => get<Claim>(`/api/claims/${id}`),
  summary:          (id: string)                                     => get<ClaimSummary>(`/api/claims/${id}/summary`),
  evidence:         (id: string)                                     => get<EvidenceSource[]>(`/api/claims/${id}/evidence`),
  audit:            (id: string)                                     => get<AuditEvent[]>(`/api/claims/${id}/audit`),
  conversation:     (id: string)                                     => get<Conversation>(`/api/claims/${id}/conversation`),
  conversationTurn: (id: string, msg: string, sessionId: string)    => post<ConversationTurnResponse>(`/api/claims/${id}/conversation/turn`, { user_message: msg, session_id: sessionId }),
  draftNote:        (id: string)                                     => get<DraftNote>(`/api/claims/${id}/draft-note`),
  approval:         (id: string)                                     => get<ApprovalRecord>(`/api/claims/${id}/approval`),
  submitApproval:   (id: string, body: ApprovalRequest)             => post<ApprovalRecord>(`/api/claims/${id}/approval`, body),
}
