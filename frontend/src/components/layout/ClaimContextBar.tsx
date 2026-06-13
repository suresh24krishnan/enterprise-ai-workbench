import { NavLink, useParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import StatusBadge from '@/components/ui/StatusBadge'
import type { Claim } from '@/types'

const TABS = [
  { label: 'Summary',    suffix: 'summary' },
  { label: 'Assistant',  suffix: 'assistant' },
  { label: 'Draft Note', suffix: 'draft-note' },
  { label: 'Approval',   suffix: 'approval' },
  { label: 'Audit',      suffix: 'audit' },
]

const COMING_SOON = new Set(['assistant', 'draft-note', 'approval'])

interface ClaimContextBarProps {
  claim: Claim
}

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export default function ClaimContextBar({ claim }: ClaimContextBarProps) {
  const { claimId } = useParams<{ claimId: string }>()

  return (
    <div className="sticky top-0 z-20 bg-white border-b border-slate-200">
      {/* Claim metadata row */}
      <div className="px-6 pt-4 pb-3 flex items-center gap-4">
        <a href="/home" className="text-slate-400 hover:text-blue-600 transition-colors flex-shrink-0">
          <ChevronLeft size={18} />
        </a>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-base font-bold text-slate-900 font-mono">{claim.claim_number}</span>
            <span className="text-slate-300">•</span>
            <span className="text-sm font-medium text-slate-700 truncate">{
              claim.parties.find(p => p.role === 'INSURED')?.name ?? '—'
            }</span>
            <span className="text-slate-300">•</span>
            <span className="text-sm text-slate-500">{claim.type.replace(/_/g, ' ')}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge variant="status" value={claim.status} />
          <StatusBadge variant="risk"   value={claim.risk_level} />
          <span className="text-sm font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
            {fmt(claim.reserve_amount)}
          </span>
        </div>
      </div>

      {/* Workflow tabs */}
      <nav className="px-6 flex gap-0 border-t border-slate-100">
        {TABS.map(({ label, suffix }) => (
          <NavLink
            key={suffix}
            to={`/claims/${claimId}/${suffix}`}
            className={({ isActive }) =>
              `relative px-4 py-2.5 text-sm font-medium transition-colors whitespace-nowrap border-b-2 -mb-px ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
              }`
            }
          >
            {label}
            {COMING_SOON.has(suffix) && (
              <span className="ml-1.5 text-[9px] bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded-full font-normal">
                soon
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
