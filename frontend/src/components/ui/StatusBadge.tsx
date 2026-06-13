type StatusVariant = 'status' | 'risk' | 'outcome'

interface StatusBadgeProps {
  variant: StatusVariant
  value: string
  className?: string
}

const statusColors: Record<string, string> = {
  OPEN:       'bg-blue-50 text-blue-700 border-blue-200',
  IN_REVIEW:  'bg-amber-50 text-amber-700 border-amber-200',
  PENDING:    'bg-slate-100 text-slate-600 border-slate-200',
  CLOSED:     'bg-slate-100 text-slate-500 border-slate-200',
  DENIED:     'bg-red-50 text-red-700 border-red-200',
}

const riskColors: Record<string, string> = {
  LOW:    'bg-emerald-50 text-emerald-700 border-emerald-200',
  MEDIUM: 'bg-amber-50  text-amber-700  border-amber-200',
  HIGH:   'bg-red-50    text-red-700    border-red-200',
}

const outcomeColors: Record<string, string> = {
  ALLOW:    'bg-emerald-50 text-emerald-700 border-emerald-200',
  ESCALATE: 'bg-amber-50  text-amber-700  border-amber-200',
  DENY:     'bg-red-50    text-red-700    border-red-200',
}

function label(variant: StatusVariant, value: string) {
  if (variant === 'risk') return `${value} RISK`
  return value.replace(/_/g, ' ')
}

export default function StatusBadge({ variant, value, className = '' }: StatusBadgeProps) {
  const colorMap = variant === 'status' ? statusColors : variant === 'risk' ? riskColors : outcomeColors
  const colors = colorMap[value] ?? 'bg-slate-100 text-slate-600 border-slate-200'

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border tracking-wide uppercase ${colors} ${className}`}
    >
      {label(variant, value)}
    </span>
  )
}
