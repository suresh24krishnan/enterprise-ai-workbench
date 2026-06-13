import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle,
  ClipboardCheck,
  MessageSquare,
  RefreshCw,
  Shield,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card, { CardHeader } from '@/components/ui/Card'
import GovernanceBadge from '@/components/ui/GovernanceBadge'
import { api } from '@/lib/api'
import type { ApprovalRecord, ApprovalRequest, ApprovalStatus, Claim } from '@/types'

// ── Status banner ─────────────────────────────────────────────────────────

function StatusBanner({ status }: { status: ApprovalStatus }) {
  const map = {
    PENDING: {
      bg: 'bg-amber-50 border-amber-200',
      text: 'text-amber-700',
      icon: <ClipboardCheck size={15} />,
      label: 'Pending Review — This note requires human approval before write-back to ClaimCenter.',
    },
    APPROVED: {
      bg: 'bg-emerald-50 border-emerald-200',
      text: 'text-emerald-700',
      icon: <CheckCircle size={15} />,
      label: 'Approved — This draft note has been approved and is ready for write-back.',
    },
    REJECTED: {
      bg: 'bg-red-50 border-red-200',
      text: 'text-red-700',
      icon: <XCircle size={15} />,
      label: 'Rejected — This draft note has been rejected and will not be written back.',
    },
    REVISION_REQUESTED: {
      bg: 'bg-violet-50 border-violet-200',
      text: 'text-violet-700',
      icon: <RefreshCw size={15} />,
      label: 'Revision Requested — The AI draft requires revision before it can be approved.',
    },
  }
  const s = map[status]
  return (
    <div className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg border text-sm font-medium ${s.bg} ${s.text}`}>
      {s.icon}
      {s.label}
    </div>
  )
}

// ── Decision radio ────────────────────────────────────────────────────────

type Decision = 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED'

function DecisionOption({
  value,
  current,
  onSelect,
  icon,
  label,
  description,
  color,
}: {
  value: Decision
  current: Decision | null
  onSelect: (v: Decision) => void
  icon: React.ReactNode
  label: string
  description: string
  color: string
}) {
  const selected = current === value
  return (
    <button
      onClick={() => onSelect(value)}
      className={`flex-1 flex flex-col items-start gap-1 p-3 rounded-xl border-2 text-left transition-all ${
        selected
          ? `${color} shadow-sm`
          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
      }`}
    >
      <div className={`flex items-center gap-2 font-semibold text-sm ${selected ? '' : 'text-slate-700'}`}>
        {icon}
        {label}
      </div>
      <p className={`text-xs leading-snug ${selected ? '' : 'text-slate-400'}`}>{description}</p>
    </button>
  )
}

// ── Checklist item ────────────────────────────────────────────────────────

function ChecklistRow({ item, passed, detail }: { item: string; passed: boolean; detail: string }) {
  return (
    <div className="flex items-start gap-2.5 py-2 border-b border-slate-100 last:border-0">
      {passed
        ? <CheckCircle size={14} className="text-emerald-500 flex-shrink-0 mt-0.5" />
        : <AlertTriangle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
      }
      <div>
        <p className="text-xs font-semibold text-slate-700">{item}</p>
        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{detail}</p>
      </div>
    </div>
  )
}

// ── Evidence row ──────────────────────────────────────────────────────────

function EvidenceRow({ title, score, rank }: { title: string; score: number; rank: number }) {
  return (
    <div className="flex items-center gap-2 py-1.5 border-b border-slate-100 last:border-0">
      <span className="text-[10px] font-bold text-slate-400 w-4 flex-shrink-0">#{rank}</span>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium text-slate-700 truncate">{title}</p>
        <div className="flex items-center gap-1.5 mt-1">
          <div className="flex-1 h-1 rounded-full bg-slate-100">
            <div className="h-1 rounded-full bg-blue-500" style={{ width: `${Math.round(score * 100)}%` }} />
          </div>
          <span className="text-[10px] text-slate-500">{Math.round(score * 100)}%</span>
        </div>
      </div>
    </div>
  )
}

// ── Metric chip ───────────────────────────────────────────────────────────

function MetricChip({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function ApprovalPage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim, setClaim] = useState<Claim | null>(null)
  const [record, setRecord] = useState<ApprovalRecord | null>(null)
  const [decision, setDecision] = useState<Decision | null>(null)
  const [comments, setComments] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([api.claim(claimId), api.approval(claimId)])
      .then(([c, a]) => {
        setClaim(c)
        setRecord(a)
        if (a.decision) setDecision(a.decision as Decision)
        if (a.reviewer_comments) setComments(a.reviewer_comments)
      })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [claimId])

  async function handleSubmit() {
    if (!claimId || !decision) return
    setSubmitting(true)
    try {
      const body: ApprovalRequest = { decision, reviewer_comments: comments }
      const updated = await api.submitApproval(claimId, body)
      setRecord(updated)
    } catch (err) {
      setError(String(err))
    } finally {
      setSubmitting(false)
    }
  }

  function handleCancel() {
    if (!record) return
    setDecision(record.decision as Decision | null)
    setComments(record.reviewer_comments)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading approval…
      </div>
    )
  }

  if (error || !claim || !record) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} /> {error ?? 'Approval not found.'}
      </div>
    )
  }

  const gov = record.governance_decision
  const note = record.draft_note
  const isDecided = record.status !== 'PENDING'
  const allPassed = record.checklist.every(c => c.passed)

  return (
    <div>
      <ClaimContextBar claim={claim} />

      <div className="p-5 space-y-4">

        {/* ── Header ── */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <ClipboardCheck size={18} className="text-blue-600" />
              AI Draft Approval
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Human-in-the-loop review required · Note ID: {record.draft_note_id}
            </p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="text-right">
              <p className="text-[10px] text-slate-400 uppercase tracking-wide font-semibold">AI Confidence</p>
              <p className="text-xl font-bold text-blue-600">
                {Math.round(note.confidence_score * 100)}%
              </p>
            </div>
            <GovernanceBadge
              outcome={gov.outcome}
              reason={gov.reason}
              policySet={`${gov.policy_set_id} v${gov.policy_set_version}`}
            />
          </div>
        </div>

        <StatusBanner status={record.status} />

        {/* ── Main 3-column grid ── */}
        <div className="grid grid-cols-3 gap-4">

          {/* ── Left+Centre: note + decision (2/3) ── */}
          <div className="col-span-2 space-y-4">

            {/* Draft note (read-only) */}
            <Card padding="none">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50">
                <div className="flex items-center gap-2">
                  <Shield size={13} className="text-violet-500" />
                  <span className="text-xs font-semibold text-slate-700">AI Generated Draft — Read Only</span>
                </div>
                <div className="flex items-center gap-4">
                  <MetricChip label="Confidence" value={`${Math.round(note.confidence_score * 100)}%`} />
                  <MetricChip label="Evidence" value={`${note.evidence_sources.length} sources`} />
                  <MetricChip label="Policy Set" value={`${gov.policy_set_id} v${gov.policy_set_version}`} />
                  <MetricChip label="Risk Level" value={claim.risk_level} />
                </div>
              </div>
              <textarea
                readOnly
                value={note.content}
                rows={14}
                className="w-full px-5 py-4 text-sm leading-relaxed text-slate-800 font-mono resize-none bg-slate-50 cursor-default focus:outline-none"
              />
            </Card>

            {/* Approval decision */}
            <Card padding="md">
              <CardHeader title="Approval Decision" subtitle="Select a decision and add reviewer comments." />

              <div className="flex gap-3 mb-4">
                <DecisionOption
                  value="APPROVED"
                  current={decision}
                  onSelect={setDecision}
                  icon={<ThumbsUp size={14} />}
                  label="Approve"
                  description="Note is accurate, policy-compliant, and ready for write-back."
                  color="border-emerald-400 bg-emerald-50 text-emerald-700"
                />
                <DecisionOption
                  value="REJECTED"
                  current={decision}
                  onSelect={setDecision}
                  icon={<ThumbsDown size={14} />}
                  label="Reject"
                  description="Note contains errors or is not suitable for write-back."
                  color="border-red-400 bg-red-50 text-red-700"
                />
                <DecisionOption
                  value="REVISION_REQUESTED"
                  current={decision}
                  onSelect={setDecision}
                  icon={<RefreshCw size={14} />}
                  label="Request Changes"
                  description="Note needs revision before it can be approved."
                  color="border-violet-400 bg-violet-50 text-violet-700"
                />
              </div>

              {/* Reviewer comments */}
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
                  <MessageSquare size={12} />
                  Reviewer Comments
                </label>
                <textarea
                  rows={3}
                  placeholder="Add review notes, corrections, or instructions for revision…"
                  value={comments}
                  onChange={e => setComments(e.target.value)}
                  disabled={isDecided}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50 disabled:cursor-not-allowed"
                />
              </div>
            </Card>

            {/* Action bar */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => void handleSubmit()}
                disabled={!decision || submitting || isDecided}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                <CheckCircle size={15} />
                {submitting ? 'Submitting…' : 'Approve and Commit'}
              </button>
              <button
                onClick={() => void handleSubmit()}
                disabled={decision !== 'REVISION_REQUESTED' || submitting || isDecided}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-violet-300 bg-violet-50 text-violet-700 text-sm font-semibold hover:bg-violet-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <RefreshCw size={15} />
                Request Revision
              </button>
              <button
                onClick={handleCancel}
                disabled={submitting || isDecided}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-slate-200 bg-white text-slate-600 text-sm font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
              {isDecided && record.decided_at && (
                <span className="text-xs text-slate-400 ml-auto">
                  Decided by {record.reviewer_name} · {new Date(record.decided_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })} UTC
                </span>
              )}
            </div>
          </div>

          {/* ── Right panel: checklist + evidence (1/3) ── */}
          <div className="space-y-4">

            <Card padding="sm">
              <CardHeader
                title="Approval Checklist"
                subtitle={allPassed ? 'All checks passed' : 'Review required'}
                actions={
                  allPassed
                    ? <CheckCircle size={14} className="text-emerald-500" />
                    : <AlertTriangle size={14} className="text-amber-400" />
                }
              />
              <div>
                {record.checklist.map(c => (
                  <ChecklistRow key={c.item} item={c.item} passed={c.passed} detail={c.detail} />
                ))}
              </div>
            </Card>

            <Card padding="sm">
              <CardHeader
                title={`Evidence Sources (${note.evidence_sources.length})`}
                subtitle="Supporting the draft note"
              />
              <div>
                {note.evidence_sources.map((src, i) => (
                  <EvidenceRow
                    key={src.source_id}
                    title={src.title}
                    score={src.relevance_score}
                    rank={i + 1}
                  />
                ))}
              </div>
            </Card>

          </div>
        </div>
      </div>
    </div>
  )
}
