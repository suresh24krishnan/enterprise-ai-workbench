import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  Brain,
  CheckCircle,
  CheckSquare,
  ChevronDown,
  ClipboardList,
  Cpu,
  FileText,
  FolderOpen,
  Lock,
  LogIn,
  MessageSquare,
  Search,
  Server,
  Shield,
  Upload,
  User,
} from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import { api } from '@/lib/api'
import type { AuditActorType, AuditEvent, AuditEventStatus, Claim } from '@/types'

// ── Helpers ────────────────────────────────────────────────────────────────

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false, timeZone: 'UTC',
  }) + ' UTC'
}

function fmtCurrency(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

// ── Status badge ───────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, string> = {
  SUCCESS:  'bg-emerald-50 text-emerald-700 border-emerald-200',
  ALLOW:    'bg-emerald-50 text-emerald-700 border-emerald-200',
  DENY:     'bg-red-50 text-red-700 border-red-200',
  ESCALATE: 'bg-amber-50 text-amber-700 border-amber-200',
  INFO:     'bg-blue-50 text-blue-700 border-blue-200',
}

function StatusBadge({ status }: { status: AuditEventStatus | null }) {
  if (!status) return null
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wide ${STATUS_STYLES[status] ?? 'bg-slate-50 text-slate-500 border-slate-200'}`}>
      {status}
    </span>
  )
}

// ── Actor icon ─────────────────────────────────────────────────────────────

const ACTOR_ICON: Record<string, typeof User> = {
  USER:       User,
  AI:         Brain,
  GOVERNANCE: Shield,
  SYSTEM:     Server,
}

const ACTOR_RING: Record<string, string> = {
  USER:       'border-blue-300 text-blue-500 bg-blue-50',
  AI:         'border-violet-300 text-violet-500 bg-violet-50',
  GOVERNANCE: 'border-emerald-300 text-emerald-600 bg-emerald-50',
  SYSTEM:     'border-slate-300 text-slate-500 bg-slate-50',
}

// ── Event icon ─────────────────────────────────────────────────────────────

const EVENT_ICON: Record<string, typeof LogIn> = {
  'user.login':                    LogIn,
  'claim.selected':                FolderOpen,
  'governance.evaluated':          Shield,
  'ai.rag.retrieved':              Search,
  'model.routed':                  Cpu,
  'ai.summary.generated':          Brain,
  'ai.conversation.turn_completed': MessageSquare,
  'ai.note.drafted':               FileText,
  'human.approval.granted':        CheckCircle,
  'claimcenter.note.written':      CheckSquare,
}

const EVENT_LABEL: Record<string, string> = {
  'user.login':                    'User Login',
  'claim.selected':                'Claim Opened',
  'governance.evaluated':          'Governance Evaluated',
  'ai.rag.retrieved':              'Evidence Retrieved',
  'model.routed':                  'Model Routed',
  'ai.summary.generated':          'AI Summary Generated',
  'ai.conversation.turn_completed': 'Assistant Response',
  'ai.note.drafted':               'Draft Note Created',
  'human.approval.granted':        'Human Approved',
  'claimcenter.note.written':      'Awaiting Governed Write Enablement',
}

// ── Chip ──────────────────────────────────────────────────────────────────

function Chip({ label, value }: { label: string; value: string | number }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] bg-slate-50 border border-slate-200 text-slate-600 px-2 py-0.5 rounded font-mono">
      <span className="text-slate-400">{label}:</span>
      <span className="font-semibold">{String(value)}</span>
    </span>
  )
}

// ── Metric card ────────────────────────────────────────────────────────────

function Metric({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 px-3 py-2.5">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide leading-none mb-1">{label}</p>
      <p className="text-xl font-bold text-slate-900 leading-none">{value}</p>
      {sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

// ── Timeline event card ────────────────────────────────────────────────────

function TimelineCard({ event, expanded, onToggle, isLast }: {
  event: AuditEvent
  expanded: boolean
  onToggle: () => void
  isLast: boolean
}) {
  const EventIcon  = EVENT_ICON[event.event_type] ?? ClipboardList
  const ActorIcon  = ACTOR_ICON[(event.actor_type as AuditActorType) ?? 'SYSTEM'] ?? Server
  const actorRing  = ACTOR_RING[(event.actor_type as string) ?? 'SYSTEM'] ?? ACTOR_RING['SYSTEM']
  const label      = EVENT_LABEL[event.event_type] ?? event.event_type

  return (
    <div className="flex gap-3">
      {/* Timeline spine */}
      <div className="flex flex-col items-center flex-shrink-0" style={{ width: '32px' }}>
        <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${actorRing}`}>
          <EventIcon size={13} />
        </div>
        {!isLast && <div className="w-px flex-1 bg-slate-200 my-1" />}
      </div>

      {/* Card */}
      <div className={`flex-1 ${isLast ? 'pb-0' : 'pb-3'}`}>
        <div
          className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden cursor-pointer select-none hover:border-slate-300 transition-colors"
          onClick={onToggle}
        >
          {/* Header row */}
          <div className="flex items-start gap-3 px-4 py-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-semibold text-slate-900">{label}</p>
                <StatusBadge status={event.status} />
              </div>
              <div className="flex items-center flex-wrap gap-x-2 gap-y-0.5 mt-1">
                <span className="text-[11px] font-mono text-slate-400">{fmtTime(event.occurred_at)}</span>
                {event.actor_name && (
                  <>
                    <span className="text-slate-300">·</span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-500">
                      <ActorIcon size={10} />
                      {event.actor_name}
                    </span>
                  </>
                )}
                {event.latency_ms != null && (
                  <>
                    <span className="text-slate-300">·</span>
                    <span className="text-[11px] text-slate-400">{event.latency_ms}ms</span>
                  </>
                )}
                {event.model_id && (
                  <>
                    <span className="text-slate-300">·</span>
                    <span className="text-[11px] font-mono text-violet-600">{event.model_id}</span>
                  </>
                )}
              </div>
            </div>
            <ChevronDown
              size={15}
              className={`text-slate-400 flex-shrink-0 mt-0.5 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            />
          </div>

          {/* Expandable detail */}
          <div className={`overflow-hidden transition-all duration-300 ${expanded ? 'max-h-96' : 'max-h-0'}`}>
            <div className="px-4 pb-4 border-t border-slate-100 pt-3 space-y-3">
              {event.description && (
                <p className="text-xs text-slate-600 leading-relaxed">{event.description}</p>
              )}
              <div className="flex flex-wrap gap-1.5">
                {event.evidence_count != null && (
                  <Chip label="evidence" value={`${event.evidence_count} sources`} />
                )}
                {event.confidence != null && (
                  <Chip label="confidence" value={`${Math.round(event.confidence * 100)}%`} />
                )}
                {event.policy_set && (
                  <Chip label="policy" value={event.policy_set} />
                )}
                {event.routing_reason && (
                  <Chip label="route" value={event.routing_reason} />
                )}
                {event.input_tokens != null && (
                  <Chip label="tokens" value={`${event.input_tokens}↑ ${event.output_tokens ?? 0}↓`} />
                )}
                {event.task_type && (
                  <Chip label="task" value={event.task_type} />
                )}
                {event.governance_outcome && (
                  <Chip label="governance" value={event.governance_outcome} />
                )}
                {Object.entries(event.payload).map(([k, v]) => (
                  <Chip key={k} label={k} value={String(v)} />
                ))}
              </div>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[10px] font-mono text-slate-300">{event.event_id}</span>
                <span className="text-slate-200">·</span>
                <span className="text-[10px] font-mono text-slate-300">{event.session_id}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Execution path step ────────────────────────────────────────────────────

function PathStep({ label, done }: { label: string; done: boolean }) {
  return (
    <div className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0">
      {done
        ? <CheckCircle size={13} className="text-emerald-500 flex-shrink-0" />
        : <div className="w-[13px] h-[13px] rounded-full border-2 border-slate-300 flex-shrink-0" />
      }
      <span className={`text-[11px] ${done ? 'text-slate-700 font-medium' : 'text-slate-400'}`}>{label}</span>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AuditTimelinePage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim,   setClaim]   = useState<Claim | null>(null)
  const [events,  setEvents]  = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([api.claim(claimId), api.audit(claimId)])
      .then(([c, e]) => { setClaim(c); setEvents(e) })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [claimId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading audit trail…
      </div>
    )
  }

  if (error || !claim) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} /> {error ?? 'Claim not found.'}
      </div>
    )
  }

  // ── Derived metrics ──────────────────────────────────────────────────────
  const aiEvents      = events.filter(e => e.actor_type === 'AI').length
  const humanEvents   = events.filter(e => e.actor_type === 'USER').length
  const govDecisions  = events.filter(e => e.actor_type === 'GOVERNANCE').length
  const totalEvidence = events.reduce((s, e) => s + (e.evidence_count ?? 0), 0)
  const modelCalls    = events.filter(e => e.model_id != null).length
  const latencies     = events.map(e => e.latency_ms).filter((v): v is number => v != null)
  const avgLatency    = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0
  const confidences   = events.map(e => e.confidence).filter((v): v is number => v != null)
  const avgConfidence = confidences.length ? Math.round(confidences.reduce((a, b) => a + b, 0) / confidences.length * 100) : 0
  const govViolations = events.filter(e => e.governance_outcome === 'DENY' || e.governance_outcome === 'ESCALATE').length

  const insured = claim.parties.find(p => p.role === 'INSURED')
  const adjuster = 'John Smith'

  // ── Execution path (inferred from events present) ─────────────────────
  const hasEvent = (t: string) => events.some(e => e.event_type === t)
  const executionPath = [
    { label: 'User authenticated',         done: hasEvent('user.login') },
    { label: 'Claim opened',               done: hasEvent('claim.selected') },
    { label: 'Governance check (summary)', done: events.some(e => e.event_type === 'governance.evaluated' && e.task_type === 'claim_summary') },
    { label: 'Evidence retrieved (RAG)',   done: hasEvent('ai.rag.retrieved') },
    { label: 'Model routed',               done: hasEvent('model.routed') },
    { label: 'AI summary generated',       done: hasEvent('ai.summary.generated') },
    { label: 'Governance check (assistant)', done: events.some(e => e.event_type === 'governance.evaluated' && e.task_type === 'claim_assistant') },
    { label: 'Draft note created',         done: hasEvent('ai.note.drafted') },
    { label: 'Human approval granted',     done: hasEvent('human.approval.granted') },
    { label: 'Awaiting Governed Write Enablement', done: hasEvent('claimcenter.note.written') },
  ]

  function toggleExpand(id: string) {
    setExpanded(prev => prev === id ? null : id)
  }

  return (
    <div>
      <ClaimContextBar claim={claim} />

      <div className="flex gap-4 p-4 h-[calc(100vh-108px)] overflow-hidden">

        {/* ── Left panel: claim context ── */}
        <div className="w-52 flex-shrink-0 overflow-y-auto space-y-3">

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-3 space-y-3">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Claim Context</p>

            <div className="space-y-2">
              {[
                { label: 'Claim #',   value: claim.claim_number },
                { label: 'Insured',   value: insured?.name ?? '—' },
                { label: 'Status',    value: claim.status },
                { label: 'Risk',      value: claim.risk_level },
                { label: 'Reserve',   value: fmtCurrency(claim.reserve_amount) },
                { label: 'Adjuster',  value: adjuster },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">{label}</p>
                  <p className="text-xs font-semibold text-slate-800 truncate">{value}</p>
                </div>
              ))}
            </div>

            <div className="pt-1 border-t border-slate-100">
              <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200">
                <Shield size={11} className="text-emerald-600 flex-shrink-0" />
                <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">Governance Active</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-3 space-y-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Session</p>
            {[
              { label: 'Session ID',  value: 'sess-mock-001' },
              { label: 'Model',       value: 'mock-standard' },
              { label: 'Policy Set',  value: 'mvp_policy_set' },
              { label: 'Policy Ver.', value: 'v1.0' },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">{label}</p>
                <p className="text-[11px] font-mono text-slate-700 truncate">{value}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-3 space-y-1">
            <div className="flex items-center gap-1.5 mb-2">
              <Lock size={10} className="text-slate-400" />
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Immutable Record</p>
            </div>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              All events are append-only. No event can be modified or deleted after recording.
            </p>
          </div>
        </div>

        {/* ── Center panel: timeline ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Timeline header */}
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div>
              <h1 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <ClipboardList size={16} className="text-blue-600" />
                Immutable AI Audit Trail
              </h1>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {events.length} events · sess-mock-001 · Click any event to expand
              </p>
            </div>
            <span className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-1 rounded-md">
              <Lock size={10} /> Append-only
            </span>
          </div>

          {/* Scrollable event list */}
          <div className="flex-1 overflow-y-auto space-y-0 pr-1">
            {events.map((event, i) => (
              <TimelineCard
                key={event.event_id}
                event={event}
                expanded={expanded === event.event_id}
                onToggle={() => toggleExpand(event.event_id)}
                isLast={i === events.length - 1}
              />
            ))}
          </div>
        </div>

        {/* ── Right panel: metrics + execution path ── */}
        <div className="w-52 flex-shrink-0 overflow-y-auto space-y-3">

          {/* Metrics grid */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Audit Summary</p>
            <div className="grid grid-cols-2 gap-1.5">
              <Metric label="Total Events"  value={events.length} />
              <Metric label="AI Events"     value={aiEvents} />
              <Metric label="Human Events"  value={humanEvents} />
              <Metric label="Gov. Checks"   value={govDecisions} />
              <Metric label="Evidence"      value={`${totalEvidence}`} sub="sources retrieved" />
              <Metric label="Model Calls"   value={modelCalls} />
              <Metric label="Avg Latency"   value={`${avgLatency}ms`} />
              <Metric label="Avg Confidence" value={`${avgConfidence}%`} />
              <Metric
                label="Policy Violations"
                value={govViolations}
                sub={govViolations === 0 ? 'none detected' : 'review required'}
              />
            </div>
          </div>

          {/* Execution path */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-3">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Execution Path</p>
            {executionPath.map(step => (
              <PathStep key={step.label} label={step.label} done={step.done} />
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
