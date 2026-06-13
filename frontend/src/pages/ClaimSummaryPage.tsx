import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Brain, AlertTriangle, Cpu } from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card, { CardHeader } from '@/components/ui/Card'
import MetricCard from '@/components/ui/MetricCard'
import GovernanceBadge from '@/components/ui/GovernanceBadge'
import EvidenceSourceCard from '@/components/ui/EvidenceSourceCard'
import { api } from '@/lib/api'
import type { Claim, ClaimSummary, EvidenceSource } from '@/types'

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 mt-5 first:mt-0">
      {children}
    </h3>
  )
}

function BulletList({ items, color = 'bg-slate-400' }: { items: string[]; color?: string }) {
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700 leading-relaxed">
          <span className={`w-1.5 h-1.5 rounded-full ${color} mt-1.5 flex-shrink-0`} />
          {item}
        </li>
      ))}
    </ul>
  )
}

export default function ClaimSummaryPage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim,    setClaim]    = useState<Claim | null>(null)
  const [summary,  setSummary]  = useState<ClaimSummary | null>(null)
  const [evidence, setEvidence] = useState<EvidenceSource[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([
      api.claim(claimId),
      api.summary(claimId),
      api.evidence(claimId),
    ])
      .then(([c, s, e]) => { setClaim(c); setSummary(s); setEvidence(e) })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [claimId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading claim…
      </div>
    )
  }

  if (error || !claim || !summary) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} />
        {error ?? 'Claim not found.'}
      </div>
    )
  }

  const gov = summary.governance_decision
  const route = summary.model_route_decision

  return (
    <div>
      <ClaimContextBar claim={claim} />

      <div className="p-6 space-y-5">

        {/* Metrics + governance row */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Evidence Score"
            value={summary.evidence_score}
            sub={`${summary.sources_used} sources retrieved`}
            icon={<Brain size={20} />}
            accentColor="emerald"
          />
          <MetricCard
            label="AI Confidence"
            value={`${Math.round(summary.confidence_score * 100)}%`}
            sub={summary.confidence_rationale.slice(0, 55) + '…'}
            accentColor="blue"
          />
          <MetricCard
            label="Sources Used"
            value={summary.sources_used}
            sub="Retrieved from knowledge base"
            accentColor="violet"
          />
          <GovernanceBadge
            outcome={gov.outcome}
            reason={gov.reason}
            policySet={`${gov.policy_set_id} v${gov.policy_set_version}`}
            className="h-full"
          />
        </div>

        {/* Main 2-column layout */}
        <div className="grid grid-cols-3 gap-5">

          {/* AI Summary — 2/3 width */}
          <Card padding="lg" className="col-span-2">
            <CardHeader
              title="AI Claim Summary"
              subtitle={`Generated ${new Date(summary.generated_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })} UTC · ${route.model_id}`}
              actions={
                <span className="flex items-center gap-1.5 text-[10px] font-semibold text-violet-600 bg-violet-50 border border-violet-200 px-2 py-1 rounded-md">
                  <Brain size={11} /> AI Generated
                </span>
              }
            />

            <SectionHeading>Incident Summary</SectionHeading>
            <p className="text-sm text-slate-700 leading-relaxed">{summary.summary}</p>

            <SectionHeading>Coverage Analysis</SectionHeading>
            <p className="text-sm text-slate-700 leading-relaxed">{summary.coverage_analysis}</p>

            <SectionHeading>Key Findings</SectionHeading>
            <BulletList items={summary.key_findings} color="bg-blue-400" />

            <SectionHeading>Open Issues</SectionHeading>
            <BulletList items={summary.open_issues} color="bg-amber-400" />

            <SectionHeading>Recommended Actions</SectionHeading>
            <BulletList items={summary.recommended_actions} color="bg-emerald-500" />

            <SectionHeading>Risk Indicators</SectionHeading>
            <BulletList items={summary.risk_indicators} color="bg-red-400" />
          </Card>

          {/* Evidence Sources — 1/3 width */}
          <div className="space-y-3">
            <Card padding="sm">
              <CardHeader
                title={`Evidence Sources (${evidence.length})`}
                subtitle="Ranked by relevance"
              />
              <div className="space-y-2">
                {evidence.map((src, i) => (
                  <EvidenceSourceCard key={src.source_id} source={src} rank={i + 1} />
                ))}
              </div>
            </Card>
          </div>
        </div>

        {/* Model routing footer */}
        <Card padding="sm">
          <div className="flex items-center gap-3">
            <Cpu size={14} className="text-slate-400 flex-shrink-0" />
            <div className="flex items-center gap-6 text-xs text-slate-500 flex-wrap">
              <span><span className="font-semibold text-slate-700">Model:</span> {route.model_id}</span>
              <span><span className="font-semibold text-slate-700">Provider:</span> {route.provider_id}</span>
              <span><span className="font-semibold text-slate-700">Tier:</span> {route.model_tier}</span>
              <span><span className="font-semibold text-slate-700">Routed by:</span> {route.routing_reason.replace(/_/g, ' ')}</span>
              <span className="flex-1 text-slate-400 italic">{route.routing_rationale}</span>
            </div>
          </div>
        </Card>

      </div>
    </div>
  )
}
