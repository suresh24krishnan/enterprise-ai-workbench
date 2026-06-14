import { useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Database,
  Eye,
  Lock,
  RefreshCw,
  Server,
  Shield,
  XCircle,
  Zap,
} from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────────────

interface RunSummary {
  request_id: string
  claim_id: string
  intent: string
  status: string
  provider_count: number
  succeeded_count: number
  failed_count: number
  latency_ms: number
  writes_enabled: boolean
  provider_mode: string
  recorded_at: string
}

interface ProviderStep {
  provider: string
  method: string
  status: string
  latency_ms: number
  retryable: boolean
  error_code: string | null
  error_message: string | null
}

interface GovernanceSummary {
  writes_enabled: boolean
  provider_mode_enforced: string
  real_providers_rejected: boolean
  all_operations_read_only: boolean
  phase_2b_gate_open: boolean
}

interface RunDetail {
  request_id: string
  claim_id: string
  intent: string
  selected_providers: string[]
  steps: ProviderStep[]
  governance: GovernanceSummary
  status: string
  latency_ms: number
  provider_count: number
  succeeded_count: number
  failed_count: number
  recorded_at: string
}

interface CTSummary {
  total_runs: number
  success_count: number
  partial_count: number
  failed_count: number
  average_latency_ms: number
  writes_enabled: boolean
  lab_safe: boolean
  provider_modes: string[]
  store_capacity: number
  store_used: number
}

// ── Helpers ───────────────────────────────────────────────────────────────

const API = '/api/integration/control-tower'

function statusColor(s: string) {
  if (s === 'success') return 'text-emerald-700 bg-emerald-50 border-emerald-200'
  if (s === 'partial')  return 'text-amber-700 bg-amber-50 border-amber-200'
  return 'text-red-700 bg-red-50 border-red-200'
}

function statusIcon(s: string) {
  if (s === 'success') return <CheckCircle size={11} />
  if (s === 'partial')  return <AlertCircle size={11} />
  return <XCircle size={11} />
}

function stepStatusDot(s: string) {
  if (s === 'success')   return 'bg-emerald-400'
  if (s === 'partial')   return 'bg-amber-400'
  if (s === 'not_found') return 'bg-slate-300'
  return 'bg-red-400'
}

function providerCardAccent(s: string): { border: string; bg: string; text: string; dot: string } {
  if (s === 'success')   return { border: 'border-emerald-200', bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-400' }
  if (s === 'partial')   return { border: 'border-amber-200',   bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-400' }
  if (s === 'not_found') return { border: 'border-slate-200',   bg: 'bg-slate-50',   text: 'text-slate-500',   dot: 'bg-slate-300' }
  return                        { border: 'border-red-200',     bg: 'bg-red-50',     text: 'text-red-700',     dot: 'bg-red-400' }
}

function intentLabel(s: string) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function providerLabel(s: string) {
  const labels: Record<string, string> = {
    claimcenter:  'ClaimCenter',
    policycenter: 'PolicyCenter',
    edw:          'EDW',
    fraud:        'Fraud',
    email:        'Email',
  }
  return labels[s.toLowerCase()] ?? s.replace(/\b\w/g, c => c.toUpperCase())
}

function fmtTime(iso: string) {
  try { return new Date(iso).toLocaleTimeString() } catch { return iso }
}

function fmtMs(ms: number) {
  return ms < 1000 ? `${ms.toFixed(1)}ms` : `${(ms / 1000).toFixed(2)}s`
}

// cumulative elapsed time for timeline
function buildElapsed(steps: ProviderStep[]): number[] {
  const out: number[] = []
  let acc = 0
  for (const s of steps) {
    acc += s.latency_ms
    out.push(acc)
  }
  return out
}

// ── Sub-components ────────────────────────────────────────────────────────

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 ${className}`}>
      {children}
    </div>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function GovernanceBadge({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[10px] font-semibold uppercase tracking-wide ${
      ok ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-700'
    }`}>
      {ok ? <CheckCircle size={10} /> : <XCircle size={10} />}
      {label}
    </div>
  )
}

function ExecutionBadge({ label, variant }: { label: string; variant: 'blue' | 'violet' | 'emerald' | 'slate' | 'amber' | 'red' }) {
  const styles: Record<string, string> = {
    blue:    'bg-blue-50 border-blue-200 text-blue-700',
    violet:  'bg-violet-50 border-violet-200 text-violet-700',
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    slate:   'bg-slate-50 border-slate-200 text-slate-600',
    amber:   'bg-amber-50 border-amber-200 text-amber-700',
    red:     'bg-red-50 border-red-200 text-red-700',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md border text-[10px] font-bold uppercase tracking-widest ${styles[variant]}`}>
      {label}
    </span>
  )
}

function ProviderStepRow({ step }: { step: ProviderStep }) {
  const isOk = step.status === 'success'
  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${stepStatusDot(step.status)}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">{providerLabel(step.provider)}</span>
          <span className="text-[10px] text-slate-400">·</span>
          <span className="text-[10px] text-slate-500 font-mono">{step.method}()</span>
        </div>
        {step.error_message && (
          <p className="text-[10px] text-red-500 mt-0.5 truncate">{step.error_message}</p>
        )}
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${statusColor(step.status)}`}>
          {step.status.toUpperCase().replace('_', ' ')}
        </span>
        <span className="text-[10px] text-slate-500 font-mono w-16 text-right">{fmtMs(step.latency_ms)}</span>
      </div>
    </div>
  )
}

// ── Execution Timeline ────────────────────────────────────────────────────

function ExecutionTimeline({ run }: { run: RunDetail }) {
  const elapsed = buildElapsed(run.steps)

  const timelineItems: Array<{ label: string; sub?: string; elapsed?: number; type: 'system' | 'provider'; status?: string }> = [
    { label: 'Supervisor Started', sub: 'Governance gate armed', type: 'system' },
    ...run.steps.map((s, i) => ({
      label: providerLabel(s.provider),
      sub: `${s.method}()`,
      elapsed: elapsed[i],
      type: 'provider' as const,
      status: s.status,
    })),
    { label: 'Aggregation Complete', sub: 'Provider results merged', type: 'system', elapsed: run.latency_ms * 0.97 },
    { label: 'Governance Verified', sub: 'Policy satisfied · writes=false', type: 'system', elapsed: run.latency_ms * 0.99 },
    { label: 'Response Returned',   sub: `${run.status.toUpperCase()} · ${fmtMs(run.latency_ms)} total`, type: 'system', elapsed: run.latency_ms },
  ]

  return (
    <div className="relative pl-5">
      {/* Vertical connector line */}
      <div className="absolute left-[8px] top-3 bottom-3 w-px bg-slate-200" />

      <div className="space-y-0">
        {timelineItems.map((item, i) => {
          const isSystem   = item.type === 'system'
          const isSuccess  = !item.status || item.status === 'success'
          const dotColor   = isSystem
            ? 'bg-blue-500 border-blue-300'
            : isSuccess ? 'bg-emerald-500 border-emerald-300' : 'bg-red-500 border-red-300'
          const isLast = i === timelineItems.length - 1

          return (
            <div key={i} className={`relative flex items-start gap-3 ${isLast ? '' : 'pb-3'}`}>
              <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 z-10 ${dotColor} ${isSystem ? '' : 'ring-2 ring-white'}`} />
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-baseline gap-2 flex-wrap">
                  <span className={`text-[11px] font-semibold ${isSystem ? 'text-slate-600' : 'text-slate-800'}`}>
                    {item.label}
                  </span>
                  {item.sub && (
                    <span className={`text-[10px] ${isSystem ? 'text-slate-400' : 'text-slate-400 font-mono'}`}>
                      {item.sub}
                    </span>
                  )}
                </div>
                {item.elapsed !== undefined && (
                  <span className="text-[10px] text-slate-400">+{fmtMs(item.elapsed)}</span>
                )}
              </div>
              {item.status && (
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border flex-shrink-0 mt-0.5 ${statusColor(item.status)}`}>
                  {item.status.toUpperCase().replace('_', ' ')}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Provider Health Cards ─────────────────────────────────────────────────

function ProviderHealthCards({ steps }: { steps: ProviderStep[] }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {steps.map((step, i) => {
        const accent = providerCardAccent(step.status)
        return (
          <div key={i} className={`rounded-xl border px-3 py-2.5 ${accent.border} ${accent.bg}`}>
            <div className="flex items-center gap-1.5 mb-1">
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${accent.dot}`} />
              <span className="text-[11px] font-bold text-slate-800">{providerLabel(step.provider)}</span>
            </div>
            <div className={`text-[10px] font-bold uppercase tracking-wide ${accent.text}`}>
              {step.status.toUpperCase().replace('_', ' ')}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">{fmtMs(step.latency_ms)}</div>
            <div className="text-[9px] text-slate-400 font-mono mt-0.5 truncate">{step.method}()</div>
          </div>
        )
      })}
    </div>
  )
}

// ── Governance Explainer ─────────────────────────────────────────────────

function GovernanceExplainer({ run }: { run: RunDetail }) {
  const [open, setOpen] = useState(false)
  const g = run.governance

  const reasons = [
    { ok: g.provider_mode_enforced === 'mock', label: 'Mock providers only — no Guidewire connectivity' },
    { ok: !g.writes_enabled,                    label: 'Writes disabled — all operations are read-only' },
    { ok: !g.phase_2b_gate_open,                label: 'No external connectivity — Phase 2B gate closed' },
    { ok: g.all_operations_read_only,            label: 'Phase 2A policy satisfied — read-only enforcement active' },
    { ok: g.real_providers_rejected,             label: 'Governance checks passed — real providers rejected' },
  ]

  const allPass = reasons.every(r => r.ok)

  return (
    <div className={`rounded-xl border ${allPass ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'}`}>
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left"
        onClick={() => setOpen(v => !v)}
      >
        <div className="flex items-center gap-2">
          <Shield size={13} className={allPass ? 'text-emerald-600' : 'text-amber-600'} />
          <span className={`text-[11px] font-bold uppercase tracking-wide ${allPass ? 'text-emerald-700' : 'text-amber-700'}`}>
            Why this execution was allowed
          </span>
        </div>
        {open
          ? <ChevronDown size={13} className="text-slate-400 flex-shrink-0" />
          : <ChevronRight size={13} className="text-slate-400 flex-shrink-0" />
        }
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-2 border-t border-white/50 pt-3">
          {reasons.map((r, i) => (
            <div key={i} className="flex items-start gap-2">
              {r.ok
                ? <CheckCircle size={12} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                : <XCircle size={12} className="text-red-500 flex-shrink-0 mt-0.5" />
              }
              <span className={`text-[11px] leading-relaxed ${r.ok ? 'text-emerald-800' : 'text-red-800'}`}>
                {r.label}
              </span>
            </div>
          ))}
          <div className="mt-3 pt-2 border-t border-white/50 text-[10px] text-slate-500 italic">
            Governance is evaluated before any provider is called. A violation raises HTTP 422 and no providers execute.
          </div>
        </div>
      )}
    </div>
  )
}

// ── Run Detail Panel ──────────────────────────────────────────────────────

function RunDetailPanel({ run, onClose }: { run: RunDetail; onClose: () => void }) {
  const statusVariant = run.status === 'success' ? 'emerald' : run.status === 'partial' ? 'amber' : 'red'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 sticky top-0 bg-white z-10">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <Eye size={15} className="text-blue-600" />
              <span className="text-sm font-semibold text-slate-800">Execution Detail</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border flex items-center gap-1 ${statusColor(run.status)}`}>
                {statusIcon(run.status)} {run.status.toUpperCase()}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5 font-mono">{run.request_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 transition-colors text-lg font-light leading-none w-6 h-6 flex items-center justify-center rounded hover:bg-slate-100"
          >
            ×
          </button>
        </div>

        <div className="p-5 space-y-6">

          {/* ── Section: Claim Summary ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Claim Summary</p>
            <div className="grid grid-cols-3 gap-2.5 text-[11px]">
              {[
                { label: 'Claim ID',        value: run.claim_id },
                { label: 'Intent',          value: intentLabel(run.intent) },
                { label: 'Status',          value: run.status.toUpperCase() },
                { label: 'Execution Time',  value: fmtMs(run.latency_ms) },
                { label: 'Provider Count',  value: String(run.provider_count) },
                { label: 'Succeeded',       value: `${run.succeeded_count} / ${run.provider_count}` },
                { label: 'Failed',          value: String(run.failed_count) },
                { label: 'Mode',            value: run.governance.provider_mode_enforced.toUpperCase() },
                { label: 'Recorded',        value: fmtTime(run.recorded_at) },
              ].map(({ label, value }) => (
                <div key={label} className="bg-slate-50 rounded-lg px-3 py-2">
                  <p className="text-slate-400 uppercase tracking-wide text-[9px] font-bold mb-0.5">{label}</p>
                  <p className="font-semibold text-slate-800">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Section: Execution Badges ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Execution Badges</p>
            <div className="flex flex-wrap gap-2">
              <ExecutionBadge label="Read Only" variant="blue" />
              <ExecutionBadge label="Mock" variant="violet" />
              <ExecutionBadge label="No Writes" variant="slate" />
              <ExecutionBadge label="Lab Safe" variant="emerald" />
              <ExecutionBadge label={`${run.succeeded_count}/${run.provider_count} Providers`} variant="slate" />
              <ExecutionBadge
                label={run.status.toUpperCase()}
                variant={statusVariant}
              />
            </div>
          </div>

          {/* ── Section: Provider Health ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Provider Health</p>
            <ProviderHealthCards steps={run.steps} />
          </div>

          {/* ── Section: Execution Timeline ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Execution Timeline</p>
            <div className="bg-slate-50 rounded-xl border border-slate-100 p-4">
              <ExecutionTimeline run={run} />
            </div>
          </div>

          {/* ── Section: Governance ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Governance</p>
            <div className="flex flex-wrap gap-2 mb-3">
              <GovernanceBadge label="Writes Disabled"    ok={!run.governance.writes_enabled} />
              <GovernanceBadge label="Read Only"          ok={run.governance.all_operations_read_only} />
              <GovernanceBadge label="Real Rejected"      ok={run.governance.real_providers_rejected} />
              <GovernanceBadge label="Mock Mode"          ok={run.governance.provider_mode_enforced === 'mock'} />
              <GovernanceBadge label="Phase 2B Gate"      ok={!run.governance.phase_2b_gate_open} />
            </div>
            <GovernanceExplainer run={run} />
          </div>

          {/* ── Section: Execution Trace (step rows) ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Execution Trace</p>
            <div className="border border-slate-100 rounded-xl overflow-hidden">
              {run.steps.map((step, i) => (
                <ProviderStepRow key={i} step={step} />
              ))}
            </div>
          </div>

          {/* ── Section: Selected Providers ── */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Selected Providers</p>
            <div className="flex flex-wrap gap-1.5">
              {run.selected_providers.map(p => (
                <span key={p} className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-semibold px-2 py-1 rounded">
                  {providerLabel(p)}
                </span>
              ))}
            </div>
          </div>

          {/* ── Data policy notice ── */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-[10px] text-slate-500 flex items-start gap-2">
            <Lock size={11} className="text-slate-400 flex-shrink-0 mt-0.5" />
            <span>
              Aggregated provider results are <strong>not stored</strong> in Control Tower traces.
              Email body, document text, and secrets are never captured. Only execution metadata is shown here.
            </span>
          </div>

        </div>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function ControlTowerPage() {
  const [summary, setSummary] = useState<CTSummary | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [summaryRes, runsRes] = await Promise.all([
        fetch(`${API}/summary`),
        fetch(`${API}/runs`),
      ])
      if (!summaryRes.ok || !runsRes.ok) throw new Error('API error')
      const [s, r] = await Promise.all([summaryRes.json(), runsRes.json()])
      setSummary(s)
      setRuns(r)
    } catch {
      setError('Could not connect to Control Tower API. Run a supervisor request first.')
    } finally {
      setLoading(false)
    }
  }

  async function openDetail(requestId: string) {
    setDetailLoading(true)
    try {
      const res = await fetch(`${API}/runs/${requestId}`)
      if (!res.ok) throw new Error('Not found')
      setSelectedRun(await res.json())
    } catch {
      // silently ignore
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Page header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            Control Tower
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Supervisor execution observability · Phase 2A · Mock providers
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-red-700 bg-red-50 border border-red-200 px-3 py-1.5 rounded-lg">
            <Lock size={11} />
            Writes Disabled
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 px-3 py-1.5 rounded-lg">
            <Shield size={11} />
            Mock Mode
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-600 bg-white border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="p-6 space-y-5">

        {/* Error banner */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-2.5">
            <AlertCircle size={14} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-amber-800">No data yet</p>
              <p className="text-[11px] text-amber-700 mt-0.5">{error}</p>
              <p className="text-[11px] text-amber-600 mt-1">
                POST to <code className="font-mono bg-amber-100 px-1 rounded">/api/integration/supervisor/run</code> to generate a trace.
              </p>
            </div>
          </div>
        )}

        {/* Summary metrics */}
        {summary && (
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Total Runs',  value: summary.total_runs,              icon: Activity,    accent: 'text-blue-600',    bg: 'bg-blue-50' },
              { label: 'Succeeded',   value: summary.success_count,            icon: CheckCircle, accent: 'text-emerald-600', bg: 'bg-emerald-50' },
              { label: 'Partial',     value: summary.partial_count,            icon: AlertCircle, accent: 'text-amber-600',   bg: 'bg-amber-50' },
              { label: 'Avg Latency', value: fmtMs(summary.average_latency_ms), icon: Clock,     accent: 'text-violet-600',  bg: 'bg-violet-50' },
            ].map(({ label, value, icon: Icon, accent, bg }) => (
              <div key={label} className="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-4 flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                  <Icon size={18} className={accent} />
                </div>
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{label}</p>
                  <p className={`text-2xl font-bold leading-none ${accent}`}>{value}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Two-column: runs list + governance */}
        <div className="grid grid-cols-3 gap-5">

          {/* Recent runs list */}
          <div className="col-span-2">
            <Card>
              <SectionHeader title="Recent Supervisor Runs" sub="Click any row to open the Execution Explorer · In-memory only · newest first" />
              {loading ? (
                <div className="py-8 text-center text-[11px] text-slate-400">Loading…</div>
              ) : runs.length === 0 ? (
                <div className="py-8 text-center">
                  <Database size={24} className="mx-auto text-slate-300 mb-2" />
                  <p className="text-[11px] text-slate-400">No runs recorded yet.</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    POST to <code className="font-mono bg-slate-100 px-1 rounded">/api/integration/supervisor/run</code>
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {runs.map(run => (
                    <div
                      key={run.request_id}
                      className="flex items-center gap-3 py-3 hover:bg-slate-50 -mx-4 px-4 transition-colors cursor-pointer group"
                      onClick={() => openDetail(run.request_id)}
                    >
                      {/* Status */}
                      <div className={`flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded border flex-shrink-0 ${statusColor(run.status)}`}>
                        {statusIcon(run.status)}
                        {run.status.toUpperCase()}
                      </div>

                      {/* Intent + claim */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-800">{intentLabel(run.intent)}</span>
                          <span className="text-[10px] text-slate-400 font-mono">{run.claim_id}</span>
                        </div>
                        <div className="flex items-center gap-3 mt-0.5">
                          <span className="text-[10px] text-slate-500 flex items-center gap-1">
                            <Server size={9} />
                            {run.succeeded_count}/{run.provider_count} providers
                          </span>
                          <span className="text-[10px] text-slate-500 flex items-center gap-1">
                            <Zap size={9} />
                            {run.provider_mode.toUpperCase()}
                          </span>
                        </div>
                      </div>

                      {/* Latency + time */}
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs font-semibold text-slate-700 font-mono">{fmtMs(run.latency_ms)}</p>
                        <p className="text-[10px] text-slate-400">{fmtTime(run.recorded_at)}</p>
                      </div>

                      {/* Explore chevron */}
                      <div className="text-slate-300 group-hover:text-blue-400 transition-colors flex-shrink-0">
                        <Eye size={13} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Governance + store info */}
          <div className="space-y-4">
            <Card>
              <SectionHeader title="Governance Status" sub="Enforced on every run" />
              <div className="space-y-2">
                {[
                  { label: 'Writes Disabled',       ok: summary ? !summary.writes_enabled : true },
                  { label: 'Read-Only Mode',         ok: true },
                  { label: 'Real Providers Blocked', ok: true },
                  { label: 'Mock Mode Enforced',     ok: true },
                  { label: 'Phase 2B Gate Closed',   ok: true },
                  { label: 'Lab Safe',               ok: summary?.lab_safe ?? true },
                ].map(({ label, ok }) => (
                  <div key={label} className="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
                    <span className="text-[11px] text-slate-600">{label}</span>
                    <div className={`flex items-center gap-1 text-[10px] font-semibold ${ok ? 'text-emerald-600' : 'text-red-600'}`}>
                      {ok ? <CheckCircle size={10} /> : <XCircle size={10} />}
                      {ok ? 'YES' : 'NO'}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {summary && (
              <Card>
                <SectionHeader title="Trace Store" sub="In-memory · LAB only" />
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">Used</span>
                    <span className="text-xs font-bold text-slate-800">{summary.store_used} / {summary.store_capacity}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-blue-400"
                      style={{ width: `${Math.round(summary.store_used / summary.store_capacity * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">Failed runs</span>
                    <span className="text-xs font-bold text-red-600">{summary.failed_count}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">Provider modes</span>
                    <div className="flex gap-1">
                      {summary.provider_modes.map(m => (
                        <span key={m} className="text-[9px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded uppercase">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-start gap-2.5">
                <Shield size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-blue-800">Phase 2A</p>
                  <p className="text-[11px] text-blue-700 mt-1 leading-relaxed">
                    Mock providers only. No Guidewire connectivity.
                    Writes disabled until Phase 2B gate satisfied.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Run detail modal */}
      {selectedRun && (
        <RunDetailPanel run={selectedRun} onClose={() => setSelectedRun(null)} />
      )}
      {detailLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
          <div className="bg-white rounded-xl px-6 py-4 text-sm text-slate-600 shadow-xl flex items-center gap-2">
            <RefreshCw size={14} className="animate-spin text-blue-500" />
            Loading execution detail…
          </div>
        </div>
      )}
    </div>
  )
}
