import { Shield, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import type { GovernanceOutcome } from '@/types'

interface GovernanceBadgeProps {
  /** Pass outcome for a per-decision badge, omit for the "Governance Active" ambient badge */
  outcome?: GovernanceOutcome
  reason?: string
  policySet?: string
  className?: string
}

const outcomeConfig: Record<GovernanceOutcome, { icon: typeof CheckCircle; label: string; colors: string }> = {
  ALLOW:    { icon: CheckCircle,   label: 'GOVERNANCE: ALLOW',    colors: 'bg-emerald-50 border-emerald-200 text-emerald-700' },
  ESCALATE: { icon: AlertTriangle, label: 'GOVERNANCE: ESCALATE', colors: 'bg-amber-50  border-amber-200  text-amber-700' },
  DENY:     { icon: XCircle,       label: 'GOVERNANCE: DENY',     colors: 'bg-red-50    border-red-200    text-red-700' },
}

export default function GovernanceBadge({ outcome, reason, policySet, className = '' }: GovernanceBadgeProps) {
  // Ambient "Governance Active" badge (no outcome)
  if (!outcome) {
    return (
      <div className={`inline-flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 px-3 py-1.5 rounded-lg ${className}`}>
        <Shield size={13} className="flex-shrink-0" />
        <span className="text-xs font-semibold tracking-wide uppercase">Governance Active</span>
      </div>
    )
  }

  const { icon: Icon, label, colors } = outcomeConfig[outcome]

  return (
    <div className={`flex items-start gap-3 border rounded-xl p-4 ${colors} ${className}`}>
      <Icon size={16} className="flex-shrink-0 mt-0.5" />
      <div className="min-w-0">
        <div className="text-xs font-bold tracking-wide uppercase">{label}</div>
        {reason && <p className="text-xs mt-1 opacity-80 leading-relaxed">{reason}</p>}
        {policySet && (
          <p className="text-[10px] mt-1.5 opacity-60 font-mono">Policy set: {policySet}</p>
        )}
      </div>
    </div>
  )
}
