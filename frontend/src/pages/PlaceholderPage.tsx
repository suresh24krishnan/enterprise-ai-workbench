import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Clock } from 'lucide-react'
import ClaimContextBar from '@/components/layout/ClaimContextBar'
import Card from '@/components/ui/Card'
import { api } from '@/lib/api'
import type { Claim } from '@/types'

interface PlaceholderPageProps {
  title: string
  description: string
  step: number
}

export default function PlaceholderPage({ title, description, step }: PlaceholderPageProps) {
  const { claimId } = useParams<{ claimId: string }>()
  const [claim, setClaim] = useState<Claim | null>(null)

  useEffect(() => {
    if (claimId) api.claim(claimId).then(setClaim).catch(() => null)
  }, [claimId])

  return (
    <div>
      {claim && <ClaimContextBar claim={claim} />}

      <div className="p-6">
        <Card className="max-w-lg mx-auto mt-16 text-center" padding="lg">
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <Clock size={22} className="text-slate-400" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 mb-2">{title}</h2>
          <p className="text-sm text-slate-500 leading-relaxed mb-4">{description}</p>
          <span className="inline-flex items-center text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1.5 rounded-full">
            Implemented in Step {step}
          </span>
        </Card>
      </div>
    </div>
  )
}
