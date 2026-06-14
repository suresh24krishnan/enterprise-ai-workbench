import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  Brain,
  CheckCircle,
  ClipboardCopy,
  FileText,
  Pencil,
  RefreshCw,
  Shield,
  ThumbsUp,
} from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card, { CardHeader } from '@/components/ui/Card'
import GovernanceBadge from '@/components/ui/GovernanceBadge'
import { api } from '@/lib/api'
import type { Claim, DraftNote, EvidenceSource } from '@/types'

// ── Evidence source row in right panel ────────────────────────────────────

function EvidenceRow({ src, rank }: { src: EvidenceSource; rank: number }) {
  const pct = Math.round(src.relevance_score * 100)
  return (
    <div className="py-2 border-b border-slate-100 last:border-0">
      <div className="flex items-start gap-2">
        <span className="text-[10px] font-bold text-slate-400 mt-0.5 w-4 flex-shrink-0">
          #{rank}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-700 leading-tight truncate">
            {src.title}
          </p>
          {src.page_reference && (
            <p className="text-[10px] text-slate-400 mt-0.5">{src.page_reference}</p>
          )}
          <div className="flex items-center gap-1.5 mt-1.5">
            <div className="flex-1 h-1 rounded-full bg-slate-100">
              <div
                className="h-1 rounded-full bg-blue-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-500 font-medium">{pct}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Action button ──────────────────────────────────────────────────────────

function ActionButton({
  icon,
  label,
  onClick,
  variant = 'secondary',
  disabled = false,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'success'
  disabled?: boolean
}) {
  const base = 'inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed'
  const styles = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700',
  }
  return (
    <button className={`${base} ${styles[variant]}`} onClick={onClick} disabled={disabled}>
      {icon}
      {label}
    </button>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function DraftNotePage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim, setClaim] = useState<Claim | null>(null)
  const [note, setNote] = useState<DraftNote | null>(null)
  const [content, setContent] = useState('')
  const [editing, setEditing] = useState(false)
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([api.claim(claimId), api.draftNote(claimId)])
      .then(([c, n]) => {
        setClaim(c)
        setNote(n)
        setContent(n.content)
      })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [claimId])

  function handleApprove() {
    // Phase 2: POST to approval endpoint
    alert('Approval successfully recorded. No system-of-record update has been performed. Current runtime is read-only. Governed write-back will be enabled only after Phase 2B identity, audit, idempotency, and policy gates are satisfied.')
  }

  function handleRegenerate() {
    if (!note) return
    setContent(note.content)
    setEditing(false)
  }

  function handleEdit() {
    setEditing(true)
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading draft note…
      </div>
    )
  }

  if (error || !claim || !note) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} /> {error ?? 'Draft note not found.'}
      </div>
    )
  }

  const gov = note.governance_decision
  const isDirty = content !== note.content

  return (
    <div>
      <ClaimContextBar claim={claim} />

      <div className="p-5 space-y-4">

        {/* ── Header row ── */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <FileText size={18} className="text-blue-600" />
              AI Draft Note
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Generated {new Date(note.generated_at).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
              })} UTC · {note.model_id}
              {isDirty && <span className="ml-2 text-amber-600 font-medium">· Edited</span>}
            </p>
          </div>

          {/* Governance + confidence inline */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="text-right">
              <p className="text-[10px] text-slate-400 uppercase tracking-wide font-semibold">
                AI Confidence
              </p>
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

        {/* ── Main 2-column layout ── */}
        <div className="grid grid-cols-3 gap-4">

          {/* ── Center: editable note (2/3) ── */}
          <div className="col-span-2 space-y-3">
            <Card padding="none" className="overflow-hidden">
              {/* Card toolbar */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50">
                <div className="flex items-center gap-2">
                  <Brain size={13} className="text-violet-500" />
                  <span className="text-xs font-semibold text-slate-700">
                    AI Generated · Adjuster Note
                  </span>
                  {editing && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">
                      Editing
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                  <Shield size={11} className="text-emerald-500" />
                  Governance: ALLOW · Approval required · No write-back in Phase 2A
                </div>
              </div>

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={content}
                onChange={e => setContent(e.target.value)}
                readOnly={!editing}
                rows={20}
                className={`w-full px-5 py-4 text-sm leading-relaxed text-slate-800 font-mono resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset ${
                  editing ? 'bg-white' : 'bg-slate-50 cursor-default'
                }`}
              />
            </Card>

            {/* ── Action bar ── */}
            <div className="flex items-center gap-3">
              <ActionButton
                icon={<ThumbsUp size={15} />}
                label="Approve Draft"
                variant="success"
                onClick={handleApprove}
              />
              <ActionButton
                icon={<Pencil size={15} />}
                label={editing ? 'Done Editing' : 'Edit Draft'}
                variant={editing ? 'primary' : 'secondary'}
                onClick={() => setEditing(e => !e)}
              />
              <ActionButton
                icon={<RefreshCw size={15} />}
                label="Regenerate"
                variant="secondary"
                onClick={handleRegenerate}
                disabled={!isDirty}
              />
              <ActionButton
                icon={copied ? <CheckCircle size={15} /> : <ClipboardCopy size={15} />}
                label={copied ? 'Copied!' : 'Copy Note'}
                variant="secondary"
                onClick={() => void handleCopy()}
              />
            </div>
          </div>

          {/* ── Right panel: evidence (1/3) ── */}
          <Card padding="sm">
            <CardHeader
              title="Evidence Used"
              subtitle={`${note.evidence_sources.length} sources · Ranked by relevance`}
            />
            <div className="mt-1">
              {note.evidence_sources.map((src, i) => (
                <EvidenceRow key={src.source_id} src={src} rank={i + 1} />
              ))}
            </div>

            {/* Governance detail */}
            <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                Policy Evaluations
              </p>
              {gov.policy_evaluations.map(pe => (
                <div key={pe.rule_id} className="flex items-start gap-1.5">
                  <CheckCircle size={11} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                  <p className="text-[10px] text-slate-600 leading-tight">{pe.reason}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
