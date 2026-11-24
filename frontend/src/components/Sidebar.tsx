import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard, Ticket, FileText, MessageSquare, BarChart3, LogOut, Orbit
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/tickets', icon: Ticket, label: 'Tickets' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/ask', icon: MessageSquare, label: 'Ask AI' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 h-screen bg-white border-r border-gray-200 flex flex-col fixed left-0 top-0">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-orbit-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">O</span>
          </div>
          <span className="font-bold text-gray-900 text-lg">Orbit</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">AI Support Assistant</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-orbit-50 text-orbit-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-orbit-100 flex items-center justify-center">
            <span className="text-orbit-700 font-semibold text-xs">
              {user?.full_name?.[0]?.toUpperCase() ?? '?'}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
