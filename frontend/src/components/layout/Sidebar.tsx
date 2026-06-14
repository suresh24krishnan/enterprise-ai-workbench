import { NavLink, useLocation } from 'react-router-dom'
import {
  Activity,
  CheckSquare,
  ClipboardList,
  FileText,
  FolderOpen,
  LayoutDashboard,
  MessageSquare,
  Shield,
  User,
  LogOut,
} from 'lucide-react'

const NAV_ITEMS = [
  { label: 'Dashboard',         icon: LayoutDashboard, to: '/dashboard',      matchPrefix: '/dashboard' },
  { label: 'Claims Workbench',  icon: FolderOpen,      to: '/home',           matchPrefix: '/claims' },
  { label: 'Control Tower',     icon: Activity,        to: '/control-tower',  matchPrefix: '/control-tower' },
  { label: 'Conversations',     icon: MessageSquare,   to: null },
  { label: 'Draft Notes',       icon: FileText,        to: null },
  { label: 'Approvals',         icon: CheckSquare,     to: null },
  { label: 'Audit Trail',       icon: ClipboardList,   to: null },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-navy-900 flex flex-col z-30">

      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-white/10">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
          <Shield size={16} className="text-white" />
        </div>
        <div>
          <div className="text-white text-sm font-semibold leading-tight">AI Workbench</div>
          <div className="text-blue-400/70 text-[9px] tracking-widest uppercase mt-0.5">Enterprise</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-2 mb-2 text-[9px] font-semibold text-slate-500 uppercase tracking-widest">
          Navigation
        </p>
        {NAV_ITEMS.map(({ label, icon: Icon, to, matchPrefix }) => {
          const isActive = to !== null && (
            matchPrefix
              ? location.pathname.startsWith(matchPrefix)
              : location.pathname === to
          )
          const isDisabled = to === null

          if (isDisabled) {
            return (
              <div
                key={label}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 cursor-not-allowed select-none"
              >
                <Icon size={16} className="flex-shrink-0" />
                <span className="text-sm">{label}</span>
              </div>
            )
          }

          return (
            <NavLink
              key={label}
              to={to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-white font-medium'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              <Icon size={16} className="flex-shrink-0" />
              <span>{label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Governance badge */}
      <div className="px-3 pb-3">
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/25 rounded-lg px-3 py-2.5">
          <Shield size={12} className="text-emerald-400 flex-shrink-0" />
          <span className="text-emerald-400 text-[10px] font-semibold tracking-widest uppercase">
            Governance Active
          </span>
        </div>
      </div>

      {/* User */}
      <div className="flex items-center gap-3 px-4 py-4 border-t border-white/10">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
          <User size={14} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-white/90 text-xs font-medium truncate">John Smith</div>
          <div className="text-slate-500 text-[10px]">Adjuster</div>
        </div>
        <button
          className="text-slate-600 hover:text-slate-300 transition-colors"
          title="Sign out"
          onClick={() => window.location.replace('/login')}
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  )
}
