import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, ChevronRight, AlertTriangle } from 'lucide-react'
import TopBar from '@/components/layout/TopBar'
import Card from '@/components/ui/Card'
import StatusBadge from '@/components/ui/StatusBadge'
import GovernanceBadge from '@/components/ui/GovernanceBadge'
import { api } from '@/lib/api'
import type { ClaimListItem, Session } from '@/types'

const TYPE_LABELS: Record<string, string> = {
  AUTO_LIABILITY:       'Commercial Auto — Liability',
  AUTO_PHYSICAL_DAMAGE: 'Commercial Auto — Physical Damage',
  PROPERTY_DAMAGE:      'Property Damage',
  WORKERS_COMPENSATION: "Workers' Compensation",
  GENERAL_LIABILITY:    'General Liability',
  MEDICAL_MALPRACTICE:  'Medical Malpractice',
}

function fmtCurrency(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function fmtDate(iso: string) {
  return new Date(iso + 'T00:00:00Z').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
  })
}

export default function HomePage() {
  const navigate = useNavigate()
  const [session,  setSession]  = useState<Session | null>(null)
  const [claims,   setClaims]   = useState<ClaimListItem[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.session(), api.claims()])
      .then(([s, c]) => { setSession(s); setClaims(c) })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div>
      <TopBar
        title="Claims Workbench"
        breadcrumbs={[{ label: 'Workbench' }, { label: 'Claims' }]}
        actions={<GovernanceBadge />}
      />

      <div className="p-6 space-y-6">

        {/* Welcome */}
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            {greeting()}{session ? `, ${session.user.name}` : ''}.
          </h2>
          <p className="text-slate-500 text-sm mt-0.5">
            {session
              ? `You are signed in as ${session.user.role} · Session ${session.session_id}`
              : 'Loading session…'}
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Open Claims',        value: claims.filter(c => c.status === 'OPEN').length,       color: 'text-blue-600' },
            { label: 'High Risk Claims',   value: claims.filter(c => c.risk_level === 'HIGH').length,   color: 'text-red-600' },
            { label: 'Pending AI Drafts',  value: 0,                                                    color: 'text-amber-600' },
          ].map(({ label, value, color }) => (
            <Card key={label} className="flex items-center gap-4">
              <span className={`text-3xl font-bold ${color}`}>{value}</span>
              <span className="text-sm text-slate-500">{label}</span>
            </Card>
          ))}
        </div>

        {/* Claims table */}
        <Card padding="none">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Assigned Claims</h3>
              <p className="text-xs text-slate-400 mt-0.5">{claims.length} claim{claims.length !== 1 ? 's' : ''} — John Smith</p>
            </div>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
              Loading claims…
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-6 text-red-600 text-sm">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}

          {!loading && !error && claims.length === 0 && (
            <div className="py-16 text-center text-slate-400 text-sm">No claims assigned.</div>
          )}

          {!loading && !error && claims.length > 0 && (
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {['Claim #', 'Insured', 'Line of Business', 'Status', 'Risk', 'Reserve', 'Date of Loss', ''].map(h => (
                    <th key={h} className="text-left text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-5 py-3">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {claims.map(claim => (
                  <tr
                    key={claim.claim_id}
                    className="border-b border-slate-50 hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/claims/${claim.claim_id}/summary`)}
                  >
                    <td className="px-5 py-4">
                      <span className="font-mono text-sm font-semibold text-slate-900">{claim.claim_number}</span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                          <FolderOpen size={13} />
                        </div>
                        <span className="text-sm text-slate-800 font-medium">{claim.primary_insured_name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm text-slate-600">{TYPE_LABELS[claim.type] ?? claim.type}</span>
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge variant="status" value={claim.status} />
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge variant="risk" value={claim.risk_level} />
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-slate-800">{fmtCurrency(claim.reserve_amount)}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm text-slate-500">{fmtDate(claim.date_of_loss)}</span>
                    </td>
                    <td className="px-5 py-4">
                      <button
                        className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                        onClick={e => { e.stopPropagation(); navigate(`/claims/${claim.claim_id}/summary`) }}
                      >
                        Open <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  )
}
