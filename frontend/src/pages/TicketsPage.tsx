import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ticketApi } from '../services/api'
import type { Ticket, TicketListResponse } from '../services/api'
import { StatusBadge, PriorityBadge, CategoryBadge, formatDate } from '../components/Badges'
import { Plus, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TicketsPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<TicketListResponse | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const r = await ticketApi.list({
        page,
        page_size: 15,
        ...(statusFilter ? { status: statusFilter } : {}),
      })
      setData(r.data)
    } catch {
      toast.error('Failed to load tickets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [page, statusFilter])

  const totalPages = data ? Math.ceil(data.total / 15) : 1

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Support Tickets</h1>
          <p className="text-gray-500 text-sm mt-1">{data?.total ?? 0} total tickets</p>
        </div>
        <Link to="/tickets/new" className="btn-primary">
          <Plus size={16} /> New Ticket
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <select
          className="input w-48"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-gray-500">Title</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Category</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Priority</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-10 text-center text-gray-400">Loading…</td></tr>
            ) : data?.items.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-10 text-center text-gray-400">No tickets found.</td></tr>
            ) : data?.items.map((t) => (
              <tr
                key={t.id}
                onClick={() => navigate(`/tickets/${t.id}`)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-6 py-3 font-medium text-gray-900 max-w-xs truncate">{t.title}</td>
                <td className="px-4 py-3"><CategoryBadge category={t.category} /></td>
                <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                <td className="px-4 py-3"><PriorityBadge priority={t.priority} /></td>
                <td className="px-4 py-3 text-gray-500">{formatDate(t.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-gray-100 flex items-center justify-between">
            <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={() => setPage(p => p - 1)} disabled={page === 1}>
                <ChevronLeft size={16} />
              </button>
              <button className="btn-secondary" onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
