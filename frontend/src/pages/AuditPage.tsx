import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ClipboardList, AlertTriangle } from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card, { CardHeader } from '@/components/ui/Card'
import AuditEventRow from '@/components/ui/AuditEventRow'
import { api } from '@/lib/api'
import type { Claim, AuditEvent } from '@/types'

export default function AuditPage() {
  const { claimId } = useParams<{ claimId: string }>()

  const [claim,  setClaim]  = useState<Claim | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    if (!claimId) return
    Promise.all([api.claim(claimId), api.audit(claimId)])
      .then(([c, e]) => { setClaim(c); setEvents(e) })
      .catch(err => setError(String(err)))
      .finally(() => setLoading(false))
  }, [claimId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400 text-sm">
        Loading audit trail…
      </div>
    )
  }

  if (error || !claim) {
    return (
      <div className="flex items-center gap-2 p-8 text-red-600 text-sm">
        <AlertTriangle size={16} />
        {error ?? 'Claim not found.'}
      </div>
    )
  }

  const allowCount    = events.filter(e => e.governance_outcome === 'ALLOW').length
  const escalateCount = events.filter(e => e.governance_outcome === 'ESCALATE').length
  const denyCount     = events.filter(e => e.governance_outcome === 'DENY').length

  return (
    <div>
      <ClaimContextBar claim={claim} />

      <div className="p-6 space-y-5">

        {/* Summary stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Total Events',         value: events.length,   color: 'text-slate-800' },
            { label: 'Governance: Allow',    value: allowCount,      color: 'text-emerald-600' },
            { label: 'Governance: Escalate', value: escalateCount,   color: 'text-amber-600' },
            { label: 'Governance: Deny',     value: denyCount,       color: 'text-red-600' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-4">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1">{label}</p>
              <p className={`text-3xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* Event timeline */}
        <Card padding="lg">
          <CardHeader
            title="Audit Trail"
            subtitle={`${events.length} events · Session sess-mock-001 · Immutable record`}
            actions={
              <span className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-1 rounded-md">
                <ClipboardList size={11} /> Append-only
              </span>
            }
          />

          {events.length === 0 && (
            <p className="text-sm text-slate-400 py-8 text-center">No audit events recorded.</p>
          )}

          <div className="mt-4">
            {events.map((event, i) => (
              <AuditEventRow
                key={event.event_id}
                event={event}
                isLast={i === events.length - 1}
              />
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
