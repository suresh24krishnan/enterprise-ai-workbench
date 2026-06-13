import { FileText, BookOpen, StickyNote, ScrollText, Scale } from 'lucide-react'
import type { EvidenceSource, SourceType } from '@/types'

const sourceIcons: Record<SourceType, typeof FileText> = {
  CLAIM_DOCUMENT:  FileText,
  KNOWLEDGE_BASE:  BookOpen,
  CLAIM_NOTE:      StickyNote,
  POLICY_DOCUMENT: ScrollText,
  REGULATION:      Scale,
}

const sourceColors: Record<SourceType, string> = {
  CLAIM_DOCUMENT:  'text-blue-600 bg-blue-50',
  KNOWLEDGE_BASE:  'text-violet-600 bg-violet-50',
  CLAIM_NOTE:      'text-slate-600 bg-slate-100',
  POLICY_DOCUMENT: 'text-amber-600 bg-amber-50',
  REGULATION:      'text-red-600 bg-red-50',
}

interface EvidenceSourceCardProps {
  source: EvidenceSource
  rank: number
}

export default function EvidenceSourceCard({ source, rank }: EvidenceSourceCardProps) {
  const Icon   = sourceIcons[source.source_type]   ?? FileText
  const colors = sourceColors[source.source_type]  ?? 'text-slate-600 bg-slate-100'
  const pct    = Math.round(source.relevance_score * 100)

  return (
    <div className="border border-slate-100 rounded-lg p-3 hover:border-blue-200 hover:bg-blue-50/30 transition-colors">
      <div className="flex items-start gap-2.5">
        {/* Rank + icon */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-0.5">
          <span className="text-[9px] font-bold text-slate-400 w-5 text-center">#{rank}</span>
          <div className={`w-6 h-6 rounded-md flex items-center justify-center ${colors}`}>
            <Icon size={12} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-800 leading-tight mb-1 truncate" title={source.title}>
            {source.title}
          </p>
          <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2">{source.excerpt}</p>
          {source.page_reference && (
            <p className="text-[10px] text-slate-400 mt-1 font-mono">{source.page_reference}</p>
          )}
        </div>
      </div>

      {/* Relevance bar */}
      <div className="mt-2.5 flex items-center gap-2">
        <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-[10px] font-semibold text-slate-500 flex-shrink-0">{pct}%</span>
      </div>
    </div>
  )
}
