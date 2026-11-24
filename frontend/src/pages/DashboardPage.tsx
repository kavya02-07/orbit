import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyticsApi, ticketApi } from '../services/api'
import type { SystemStats, Ticket } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { StatusBadge, PriorityBadge, CategoryBadge, formatDate } from '../components/Badges'
import { Ticket as TicketIcon, FileText, MessageSquare, TrendingUp, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: any; color: string
}) {
  return (
    <div className="card p-6 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([])

  useEffect(() => {
    analyticsApi.stats().then((r) => setStats(r.data)).catch(() => toast.error('Failed to load stats'))
    ticketApi.list({ page_size: 5 }).then((r) => setRecentTickets(r.data.items)).catch(() => {})
  }, [])

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-gray-500 mt-1">Here's what's happening in your support workspace.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Tickets" value={stats?.total_tickets ?? '—'} icon={TicketIcon} color="bg-orbit-600" />
        <StatCard label="Documents" value={stats?.total_documents ?? '—'} icon={FileText} color="bg-green-600" />
        <StatCard label="Indexed Chunks" value={stats?.total_chunks ?? '—'} icon={TrendingUp} color="bg-purple-600" />
        <StatCard label="Open Tickets" value={stats?.tickets.by_status.open ?? '—'} icon={MessageSquare} color="bg-orange-500" />
      </div>

      {/* Recent Tickets */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Recent Tickets</h2>
          <Link to="/tickets/new" className="btn-primary">
            <Plus size={16} /> New Ticket
          </Link>
        </div>
        {recentTickets.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-400">
            <TicketIcon size={40} className="mx-auto mb-3 opacity-30" />
            <p>No tickets yet. Create your first one!</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {recentTickets.map((t) => (
              <Link key={t.id} to={`/tickets/${t.id}`} className="flex items-start gap-4 px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{t.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{formatDate(t.created_at)}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <CategoryBadge category={t.category} />
                  <StatusBadge status={t.status} />
                  <PriorityBadge priority={t.priority} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
