import { ReactNode } from 'react'

interface MetricCardProps {
  label: string
  value: string | number
  sub?: string
  icon?: ReactNode
  accentColor?: 'blue' | 'emerald' | 'violet' | 'amber'
}

const accentMap = {
  blue:    'text-blue-600',
  emerald: 'text-emerald-600',
  violet:  'text-violet-600',
  amber:   'text-amber-600',
}

export default function MetricCard({
  label,
  value,
  sub,
  icon,
  accentColor = 'blue',
}: MetricCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-4 flex items-start gap-4">
      {icon && (
        <div className={`mt-0.5 ${accentMap[accentColor]}`}>
          {icon}
        </div>
      )}
      <div>
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">{label}</p>
        <p className={`text-3xl font-bold leading-none ${accentMap[accentColor]}`}>{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-1.5">{sub}</p>}
      </div>
    </div>
  )
}
