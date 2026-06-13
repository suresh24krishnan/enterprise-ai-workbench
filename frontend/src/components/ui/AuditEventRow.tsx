import {
  LogIn, LogOut, FolderOpen, Search, Brain,
  MessageSquare, FileText, Shield, CheckCircle,
  XCircle, AlertCircle, CheckSquare, Clock,
} from 'lucide-react'
import type { AuditEvent } from '@/types'

const EVENT_META: Record<string, { icon: typeof Clock; label: string; iconColor: string }> = {
  'user.login':                    { icon: LogIn,        label: 'User Login',             iconColor: 'text-blue-500' },
  'user.logout':                   { icon: LogOut,       label: 'User Logout',            iconColor: 'text-slate-400' },
  'user.session_expired':          { icon: Clock,        label: 'Session Expired',        iconColor: 'text-slate-400' },
  'claim.selected':                { icon: FolderOpen,   label: 'Claim Selected',         iconColor: 'text-blue-500' },
  'claim.searched':                { icon: Search,       label: 'Claims Searched',        iconColor: 'text-slate-500' },
  'ai.summary.generated':          { icon: Brain,        label: 'AI Summary Generated',   iconColor: 'text-violet-500' },
  'ai.conversation.turn_completed':{ icon: MessageSquare,label: 'Conversation Turn',      iconColor: 'text-violet-500' },
  'ai.rag.retrieved':              { icon: Search,       label: 'Evidence Retrieved',     iconColor: 'text-blue-400' },
  'ai.note.drafted':               { icon: FileText,     label: 'Note Drafted',           iconColor: 'text-violet-500' },
  'governance.evaluated':          { icon: Shield,       label: 'Governance Evaluated',   iconColor: 'text-emerald-500' },
  'human.approval.requested':      { icon: AlertCircle,  label: 'Approval Requested',     iconColor: 'text-amber-500' },
  'human.approval.granted':        { icon: CheckCircle,  label: 'Approval Granted',       iconColor: 'text-emerald-500' },
  'human.approval.rejected':       { icon: XCircle,      label: 'Approval Rejected',      iconColor: 'text-red-500' },
  'claimcenter.note.written':      { icon: CheckSquare,  label: 'Note Written',           iconColor: 'text-emerald-500' },
  'claimcenter.note.write_failed': { icon: XCircle,      label: 'Write Failed',           iconColor: 'text-red-500' },
}

const outcomeChip: Record<string, string> = {
  ALLOW:    'bg-emerald-50 text-emerald-700 border-emerald-200',
  ESCALATE: 'bg-amber-50 text-amber-700 border-amber-200',
  DENY:     'bg-red-50 text-red-700 border-red-200',
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    second: '2-digit', hour12: false, timeZone: 'UTC',
  }) + ' UTC'
}

interface AuditEventRowProps {
  event: AuditEvent
  isLast?: boolean
}

export default function AuditEventRow({ event, isLast }: AuditEventRowProps) {
  const meta   = EVENT_META[event.event_type] ?? { icon: Clock, label: event.event_type, iconColor: 'text-slate-400' }
  const Icon   = meta.icon

  return (
    <div className="flex gap-4">
      {/* Timeline line + icon */}
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full bg-slate-50 border-2 border-slate-200 flex items-center justify-center flex-shrink-0 ${meta.iconColor}`}>
          <Icon size={14} />
        </div>
        {!isLast && <div className="w-px flex-1 bg-slate-200 mt-1" />}
      </div>

      {/* Content */}
      <div className={`flex-1 pb-5 ${isLast ? '' : ''}`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">{meta.label}</p>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">{event.event_type}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {event.governance_outcome && (
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase tracking-wide ${outcomeChip[event.governance_outcome] ?? ''}`}>
                {event.governance_outcome}
              </span>
            )}
          </div>
        </div>

        {/* Meta row */}
        <div className="flex items-center flex-wrap gap-3 mt-2">
          <span className="text-[11px] text-slate-400">{fmtTime(event.occurred_at)}</span>
          <span className="text-[11px] text-slate-400">·</span>
          <span className="text-[11px] text-slate-500">{event.user_id}</span>
          {event.model_id && (
            <>
              <span className="text-[11px] text-slate-400">·</span>
              <span className="text-[11px] font-mono text-slate-500">{event.model_id}</span>
            </>
          )}
          {event.latency_ms != null && (
            <>
              <span className="text-[11px] text-slate-400">·</span>
              <span className="text-[11px] text-slate-400">{event.latency_ms}ms</span>
            </>
          )}
          {event.input_tokens != null && (
            <>
              <span className="text-[11px] text-slate-400">·</span>
              <span className="text-[11px] text-slate-400">{event.input_tokens}↑ {event.output_tokens}↓ tokens</span>
            </>
          )}
        </div>

        {/* Payload highlights */}
        {Object.keys(event.payload).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {Object.entries(event.payload).map(([k, v]) => (
              <span key={k} className="text-[10px] bg-slate-50 border border-slate-200 text-slate-500 px-2 py-0.5 rounded font-mono">
                {k}: {String(v)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
