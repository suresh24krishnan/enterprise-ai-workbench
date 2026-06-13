import {
  Activity,
  Brain,
  CheckCircle,
  Clock,
  Cpu,
  DollarSign,
  FileText,
  Heart,
  Server,
  Shield,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react'

// ── Static mock analytics data ─────────────────────────────────────────────
// Replace this module with an AnalyticsService call when real telemetry is available.

const KPIS = [
  { label: 'Claims AI Assisted',      value: '2,481', sub: 'MTD',              icon: Brain,       accent: 'text-blue-600',    bg: 'bg-blue-50' },
  { label: 'Human Approval Rate',     value: '96%',   sub: '+2pp vs last month', icon: Users,       accent: 'text-emerald-600', bg: 'bg-emerald-50' },
  { label: 'Governance Allow Rate',   value: '99.2%', sub: 'Policy Engine',      icon: Shield,      accent: 'text-violet-600',  bg: 'bg-violet-50' },
  { label: 'Avg AI Confidence',       value: '93%',   sub: 'Across all tasks',   icon: TrendingUp,  accent: 'text-blue-600',    bg: 'bg-blue-50' },
  { label: 'Avg Processing Time',     value: '6.4 min', sub: 'End-to-end',       icon: Clock,       accent: 'text-amber-600',   bg: 'bg-amber-50' },
  { label: 'Est. Monthly Savings',    value: '$148K', sub: 'vs. manual baseline', icon: DollarSign,  accent: 'text-emerald-600', bg: 'bg-emerald-50' },
]

const MODEL_UTILIZATION = [
  { name: 'GPT-4.1-mini',   pct: 52, latency: '183ms', costPer: '$0.0014', bar: 'bg-blue-500' },
  { name: 'Claude Sonnet',  pct: 33, latency: '245ms', costPer: '$0.0031', bar: 'bg-violet-500' },
  { name: 'Gemini Flash',   pct: 15, latency: '121ms', costPer: '$0.0009', bar: 'bg-cyan-500' },
]

const GOVERNANCE_DIST = [
  { outcome: 'ALLOW',    pct: 96, count: 2381, border: 'border-emerald-200', bg: 'bg-emerald-50', accent: 'text-emerald-700', dot: 'bg-emerald-500', bar: 'bg-emerald-500' },
  { outcome: 'ESCALATE', pct:  3, count:   74, border: 'border-amber-200',   bg: 'bg-amber-50',   accent: 'text-amber-700',   dot: 'bg-amber-500',   bar: 'bg-amber-500' },
  { outcome: 'DENY',     pct:  1, count:   25, border: 'border-red-200',     bg: 'bg-red-50',     accent: 'text-red-700',     dot: 'bg-red-500',     bar: 'bg-red-500' },
]

const USE_CASES = [
  { name: 'Claim Summary',          count: 841, icon: FileText },
  { name: 'Coverage Analysis',      count: 623, icon: Shield },
  { name: 'Repair Estimate',        count: 512, icon: Zap },
  { name: 'Claim Assistant',        count: 398, icon: Brain },
  { name: 'Draft Note Generation',  count: 285, icon: FileText },
  { name: 'Approval Support',       count: 214, icon: CheckCircle },
]

const MAX_USE_CASE_COUNT = 841

const TIMELINE_STEPS = [
  'Login',
  'Claim Opened',
  'Governance',
  'Evidence',
  'AI Summary',
  'Assistant',
  'Draft',
  'Approval',
  'Write-back',
]

const HEALTH_ITEMS = [
  { name: 'Policy Engine',      status: 'Healthy',     ok: true  },
  { name: 'Audit Store',        status: 'Healthy',     ok: true  },
  { name: 'Model Router',       status: 'Healthy',     ok: true  },
  { name: 'Evidence Retrieval', status: 'Healthy',     ok: true  },
  { name: 'AI Governance',      status: 'Healthy',     ok: true  },
  { name: 'Platform Status',    status: 'Operational', ok: true  },
]

// ── Sub-components ─────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, icon: Icon, accent, bg }: typeof KPIS[number]) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-4 flex items-start gap-4">
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
        <Icon size={18} className={accent} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1.5">{label}</p>
        <p className={`text-2xl font-bold leading-none ${accent}`}>{value}</p>
        <p className="text-[11px] text-slate-400 mt-1">{sub}</p>
      </div>
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

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 ${className}`}>
      {children}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function ExecutiveDashboardPage() {
  return (
    <div className="min-h-screen bg-slate-50">

      {/* Page header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            AI Operations Dashboard
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Enterprise AI Workbench · Claims Division · June 13, 2026
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
            <Heart size={11} />
            All Systems Operational
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 px-3 py-1.5 rounded-lg">
            <Shield size={11} />
            Governance Active
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">

        {/* ── KPI row ── */}
        <div className="grid grid-cols-3 gap-4">
          {KPIS.map(kpi => <KpiCard key={kpi.label} {...kpi} />)}
        </div>

        {/* ── Three-column section ── */}
        <div className="grid grid-cols-3 gap-5">

          {/* ── Column 1: Model Utilization ── */}
          <div className="space-y-5">
            <Card>
              <SectionHeader title="Model Utilization" sub="Share of AI requests · Month to date" />
              <div className="space-y-4">
                {MODEL_UTILIZATION.map(m => (
                  <div key={m.name}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <Cpu size={12} className="text-slate-400" />
                        <span className="text-xs font-semibold text-slate-700">{m.name}</span>
                      </div>
                      <span className="text-xs font-bold text-slate-900">{m.pct}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100">
                      <div className={`h-2 rounded-full ${m.bar}`} style={{ width: `${m.pct}%` }} />
                    </div>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="text-[10px] text-slate-400">Avg latency: <span className="font-semibold text-slate-600">{m.latency}</span></span>
                      <span className="text-slate-300">·</span>
                      <span className="text-[10px] text-slate-400">Est. cost/req: <span className="font-semibold text-slate-600">{m.costPer}</span></span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Top AI Use Cases */}
            <Card>
              <SectionHeader title="Top AI Use Cases" sub="Request volume · MTD" />
              <div className="space-y-2.5">
                {USE_CASES.map(uc => (
                  <div key={uc.name} className="flex items-center gap-3">
                    <uc.icon size={12} className="text-slate-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-medium text-slate-700 truncate">{uc.name}</span>
                        <span className="text-[11px] font-bold text-slate-900 ml-2 flex-shrink-0">{uc.count.toLocaleString()}</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-100">
                        <div
                          className="h-1.5 rounded-full bg-blue-400"
                          style={{ width: `${Math.round(uc.count / MAX_USE_CASE_COUNT * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* ── Column 2: Governance + Timeline ── */}
          <div className="space-y-5">
            <Card>
              <SectionHeader title="Governance Distribution" sub="Policy engine outcomes · MTD" />
              <div className="space-y-3">
                {GOVERNANCE_DIST.map(g => (
                  <div key={g.outcome} className={`rounded-lg border ${g.border} ${g.bg} px-4 py-3`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${g.dot}`} />
                        <span className={`text-xs font-bold ${g.accent} uppercase tracking-wide`}>{g.outcome}</span>
                      </div>
                      <div className="flex items-baseline gap-2">
                        <span className={`text-xl font-bold ${g.accent}`}>{g.pct}%</span>
                        <span className="text-[11px] text-slate-400">{g.count.toLocaleString()} req</span>
                      </div>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-white/60">
                      <div className={`h-1.5 rounded-full ${g.bar}`} style={{ width: `${g.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Today's Execution Timeline */}
            <Card>
              <SectionHeader title="Today's Execution Timeline" sub="Last completed workflow · CLM-2026-100245" />
              <div className="space-y-0">
                {TIMELINE_STEPS.map((step, i) => (
                  <div key={step} className="flex items-start gap-3">
                    <div className="flex flex-col items-center flex-shrink-0" style={{ width: '20px' }}>
                      <div className="w-5 h-5 rounded-full bg-emerald-100 border-2 border-emerald-400 flex items-center justify-center flex-shrink-0">
                        <CheckCircle size={10} className="text-emerald-600" />
                      </div>
                      {i < TIMELINE_STEPS.length - 1 && (
                        <div className="w-px h-4 bg-emerald-200 my-0.5" />
                      )}
                    </div>
                    <div className="pb-1 pt-0.5">
                      <span className="text-[11px] font-medium text-slate-700">{step}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2">
                <CheckCircle size={12} className="text-emerald-500" />
                <span className="text-[11px] text-emerald-700 font-semibold">All 9 steps completed · 6m 12s total</span>
              </div>
            </Card>
          </div>

          {/* ── Column 3: Platform Health ── */}
          <div className="space-y-5">
            <Card>
              <SectionHeader title="Enterprise Platform Health" sub="Real-time service status" />
              <div className="space-y-1">
                {HEALTH_ITEMS.map(item => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between py-2.5 border-b border-slate-100 last:border-0"
                  >
                    <div className="flex items-center gap-2.5">
                      <Server size={12} className="text-slate-400" />
                      <span className="text-xs font-medium text-slate-700">{item.name}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="text-[11px] font-semibold text-emerald-700">{item.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Platform stats */}
            <Card>
              <SectionHeader title="Platform Metrics" sub="June 2026 · Month to date" />
              <div className="space-y-3">
                {[
                  { label: 'Total API Calls',       value: '14,892' },
                  { label: 'Policy Rules Evaluated', value: '29,784' },
                  { label: 'Evidence Retrievals',   value: '10,437' },
                  { label: 'Audit Events Recorded', value: '44,680' },
                  { label: 'Human Reviews',         value: '2,381' },
                  { label: 'Policy Violations', value: '0', sub: 'None detected', highlight: false },
                ].map(row => (
                  <div key={row.label} className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">{row.label}</span>
                    <div className="text-right">
                      <span className={`text-xs font-bold ${row.highlight ? 'text-red-600' : 'text-slate-900'}`}>
                        {row.value}
                      </span>
                      {'sub' in row && row.sub && (
                        <p className="text-[10px] text-slate-400">{row.sub}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Governance note */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-start gap-2.5">
                <Shield size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-blue-800">AI Governance Policy</p>
                  <p className="text-[11px] text-blue-700 mt-1 leading-relaxed">
                    Every AI action is evaluated against <span className="font-semibold">mvp_policy_set v1.0</span> before execution.
                    Human approval is required for all write-back operations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
