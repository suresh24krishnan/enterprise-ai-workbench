import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle,
  Lock,
  MessageSquare,
  Send,
  Shield,
  XCircle,
} from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card, { CardHeader } from '@/components/ui/Card'
import EvidenceSourceCard from '@/components/ui/EvidenceSourceCard'
import { api } from '@/lib/api'
import type { Claim, ConversationTurn, GovernanceOutcome } from '@/types'

// ── Suggested prompts ──────────────────────────────────────────────────────

const SUGGESTED_PROMPTS = [
  'What are the outstanding issues?',
  'What is the estimated total loss amount?',
  'What coverage applies?',
  'Draft a claim note',
]

// ── Sub-components ─────────────────────────────────────────────────────────

function GuardrailRow({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-emerald-700">
      <CheckCircle size={12} className="text-emerald-500 flex-shrink-0" />
      {label}
    </div>
  )
}

function GovernanceChip({ outcome }: { outcome: GovernanceOutcome }) {
  if (outcome === 'ALLOW') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle size={10} /> ALLOW
      </span>
    )
  }
  if (outcome === 'ESCALATE') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
        <AlertTriangle size={10} /> ESCALATE
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
      <XCircle size={10} /> DENY
    </span>
  )
}

function SourceChip({ title, rank }: { title: string; rank: number }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
      <span className="font-bold">#{rank}</span>
      <span className="max-w-[120px] truncate">{title}</span>
    </span>
  )
}

// Renders markdown-like bold (**text**) in the assistant message
function AssistantText({ text }: { text: string }) {
  const lines = text.split('\n')
  return (
    <div className="space-y-1.5">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />
        // Replace **bold** with <strong>
        const parts = line.split(/\*\*(.+?)\*\*/g)
        return (
          <p key={i} className="text-sm text-slate-700 leading-relaxed">
            {parts.map((part, j) =>
              j % 2 === 1 ? <strong key={j}>{part}</strong> : <span key={j}>{part}</span>
            )}
          </p>
        )
      })}
    </div>
  )
}

function UserBubble({ message }: { message: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
        {message}
      </div>
    </div>
  )
}

function AssistantBubble({ turn }: { turn: ConversationTurn }) {
  const isDenied = turn.governance_decision.outcome === 'DENY'
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        <div className={`rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border ${isDenied ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
          {isDenied && (
            <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold text-red-600">
              <Shield size={12} />
              Governance Refusal
            </div>
          )}
          <AssistantText text={turn.assistant_message} />
        </div>

        {/* Footer: governance + citations */}
        <div className="flex flex-wrap items-center gap-2 px-1">
          <GovernanceChip outcome={turn.governance_decision.outcome} />
          {turn.confidence_score > 0 && (
            <span className="text-[10px] text-slate-400">
              Confidence: {Math.round(turn.confidence_score * 100)}%
            </span>
          )}
          {turn.sources_used.map((src, i) => (
            <SourceChip key={src.source_id} title={src.title} rank={i + 1} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function AssistantPage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim, setClaim] = useState<Claim | null>(null)
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sessionId] = useState('sess-mock-001')

  // The sources from the most recent assistant turn
  const lastTurn = turns[turns.length - 1]
  const activeSources = lastTurn?.sources_used ?? []

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([api.claim(claimId), api.conversation(claimId)])
      .then(([c, conv]) => {
        setClaim(c)
        setTurns(conv.turns)
      })
      .catch(err => setLoadError(String(err)))
  }, [claimId])

  // Scroll to bottom on new turns
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  async function sendMessage(text: string) {
    if (!claimId || !text.trim() || sending) return
    setInput('')
    setSending(true)

    // Optimistic user bubble
    const optimisticTurn: ConversationTurn = {
      turn_id: `optimistic-${Date.now()}`,
      user_message: text,
      assistant_message: '',
      sources_used: [],
      governance_decision: { decision_id: '', evaluated_at: '', task_type: '', claim_id: null, outcome: 'ALLOW', reason: '', deny_reason: null, escalate_reason: null, policy_evaluations: [], policy_set_id: '', policy_set_version: '' },
      confidence_score: 0,
      refusal_reason: null,
    }
    setTurns(prev => [...prev, optimisticTurn])

    try {
      const resp = await api.conversationTurn(claimId, text, sessionId)
      const fullTurn: ConversationTurn = {
        turn_id: resp.turn_id,
        user_message: text,
        assistant_message: resp.assistant_message,
        sources_used: resp.sources_used,
        governance_decision: resp.governance_decision,
        confidence_score: resp.confidence_score,
        refusal_reason: resp.refusal_reason,
      }
      setTurns(prev => [...prev.slice(0, -1), fullTurn])
    } catch {
      setTurns(prev => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void sendMessage(input)
    }
  }

  if (loadError) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} /> {loadError}
      </div>
    )
  }

  if (!claim) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading…
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <ClaimContextBar claim={claim} />

      <div className="flex flex-1 gap-3 p-3 min-h-0 overflow-hidden">

        {/* ── Left panel: context + guardrails ── */}
        <div className="w-44 flex-shrink-0 space-y-3">

          <Card padding="sm">
            <div className="flex items-center gap-2 mb-3">
              <Lock size={13} className="text-blue-600" />
              <span className="text-xs font-semibold text-slate-700">Context Locked</span>
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-500">
              <div><span className="font-semibold text-slate-600">Claim:</span> {claimId}</div>
              <div><span className="font-semibold text-slate-600">Insured:</span> {claim.parties.find(p => p.role === 'INSURED')?.name ?? '—'}</div>
              <div><span className="font-semibold text-slate-600">Type:</span> {claim.type.replace(/_/g, ' ')}</div>
              <div><span className="font-semibold text-slate-600">Status:</span> {claim.status}</div>
            </div>
          </Card>

          <Card padding="sm">
            <CardHeader title="Guardrails" />
            <div className="space-y-2 mt-1">
              <GuardrailRow label="Source restricted" />
              <GuardrailRow label="PII protected" />
              <GuardrailRow label="Policy enforced" />
              <GuardrailRow label="All interactions audited" />
            </div>
          </Card>

          {/* Governance Active ambient badge */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200">
            <Shield size={13} className="text-emerald-600" />
            <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">
              Governance Active
            </span>
          </div>

        </div>

        {/* ── Centre: chat ── */}
        <div className="flex-1 flex flex-col min-w-0">

          <Card padding="none" className="flex-1 flex flex-col min-h-0 overflow-hidden">

            {/* Chat header */}
            <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
              <MessageSquare size={15} className="text-blue-600" />
              <span className="text-sm font-semibold text-slate-700">Claim Assistant</span>
              <span className="ml-auto text-[10px] text-slate-400">
                Scoped to {claimId} · mock-standard model
              </span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {turns.length === 0 && (
                <div className="text-center py-12 space-y-2">
                  <Shield size={32} className="text-blue-200 mx-auto" />
                  <p className="text-sm font-medium text-slate-500">
                    Governed Claim Assistant
                  </p>
                  <p className="text-xs text-slate-400 max-w-xs mx-auto">
                    Ask questions about claim {claimId}. All responses are grounded in
                    authorized claim evidence and governed before delivery.
                  </p>
                </div>
              )}

              {turns.map(turn => (
                <div key={turn.turn_id} className="space-y-3">
                  <UserBubble message={turn.user_message} />
                  {turn.assistant_message ? (
                    <AssistantBubble turn={turn} />
                  ) : (
                    <div className="flex items-center gap-2 pl-1">
                      <div className="flex gap-1">
                        {([0, 1, 2] as const).map(i => (
                          <span
                            key={`dot-${i}`}
                            className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-bounce"
                            style={{ animationDelay: `${i * 0.15}s` }}
                          />
                        ))}
                      </div>
                      <span className="text-xs text-slate-400">Thinking…</span>
                    </div>
                  )}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Suggested prompts (shown when no turns yet or always) */}
            {turns.length === 0 && (
              <div className="px-4 pb-3 flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map(prompt => (
                  <button
                    key={prompt}
                    onClick={() => void sendMessage(prompt)}
                    className="text-xs px-3 py-1.5 rounded-full border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="px-4 pb-4 pt-2 border-t border-slate-100">
              <div className="flex gap-2 items-end">
                <textarea
                  className="flex-1 resize-none rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[44px] max-h-32"
                  placeholder="Ask about this claim…"
                  rows={1}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={sending}
                />
                <button
                  onClick={() => void sendMessage(input)}
                  disabled={!input.trim() || sending}
                  className="flex-shrink-0 w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
              <p className="mt-1.5 text-[10px] text-slate-400 text-center">
                Responses are grounded in authorized claim evidence only · Press Enter to send
              </p>
            </div>
          </Card>
        </div>

        {/* ── Right panel: evidence sources ── */}
        <div className="w-44 flex-shrink-0">
          <Card padding="sm" className="h-full overflow-y-auto">
            <CardHeader
              title={`Evidence Sources ${activeSources.length > 0 ? `(${activeSources.length})` : ''}`}
              subtitle={activeSources.length > 0 ? 'From last response' : 'Send a message to see sources'}
            />
            {activeSources.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                <Shield size={24} className="mb-2 opacity-30" />
                <p className="text-xs text-center">Sources will appear here after each governed response.</p>
              </div>
            ) : (
              <div className="space-y-2 mt-2">
                {activeSources.map((src, i) => (
                  <EvidenceSourceCard key={src.source_id} source={src} rank={i + 1} />
                ))}
              </div>
            )}
          </Card>
        </div>

      </div>
    </div>
  )
}
