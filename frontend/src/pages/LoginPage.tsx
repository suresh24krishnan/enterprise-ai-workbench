import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, CheckCircle } from 'lucide-react'
import Button from '@/components/ui/Button'

const FEATURES = [
  'Governance engine evaluates every AI action',
  'Human approval required before any write',
  'Complete, immutable audit trail',
  'Evidence-grounded AI responses',
  'Model routing by task type and risk level',
]

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail]       = useState('john.smith@workbench.local')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!email) { setError('Email is required.'); return }
    setLoading(true)
    // Phase 1: mock — any credentials accepted
    setTimeout(() => navigate('/home'), 600)
  }

  return (
    <div className="min-h-screen flex">

      {/* Left panel — brand */}
      <div className="hidden lg:flex flex-col w-[45%] bg-navy-900 p-12 justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center">
            <Shield size={18} className="text-white" />
          </div>
          <div>
            <div className="text-white font-bold text-lg leading-tight">AI Workbench</div>
            <div className="text-blue-400/60 text-[10px] tracking-widest uppercase">Enterprise</div>
          </div>
        </div>

        <div>
          <h2 className="text-4xl font-bold text-white leading-tight mb-4">
            Governed AI<br />for Claims.
          </h2>
          <p className="text-slate-400 text-base mb-10 leading-relaxed">
            Every AI action is evaluated, grounded in evidence,<br />
            and requires human authority before writing.
          </p>
          <ul className="space-y-3">
            {FEATURES.map(f => (
              <li key={f} className="flex items-start gap-3">
                <CheckCircle size={15} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                <span className="text-slate-300 text-sm">{f}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3">
          <Shield size={13} className="text-emerald-400" />
          <span className="text-emerald-400 text-xs font-semibold tracking-widest uppercase">
            Governance Active — Phase 1 MVP
          </span>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Shield size={16} className="text-white" />
            </div>
            <span className="font-bold text-slate-900">Enterprise AI Workbench</span>
          </div>

          <h1 className="text-2xl font-bold text-slate-900 mb-1">Sign in</h1>
          <p className="text-slate-500 text-sm mb-8">Access the Claims AI Workbench.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Email address
              </label>
              <input
                type="text"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-red-600 text-xs">{error}</p>
            )}

            <Button type="submit" variant="primary" size="lg" className="w-full" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign In'}
            </Button>
          </form>

          {/* Demo credentials */}
          <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Phase 1 — Demo credentials
            </p>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Email</span>
                <span className="font-mono text-slate-700">john.smith@workbench.local</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Password</span>
                <span className="font-mono text-slate-400">any value</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Role</span>
                <span className="font-mono text-slate-700">ADJUSTER</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
