import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ticketApi } from '../services/api'
import type { Ticket } from '../services/api'
import { StatusBadge, PriorityBadge, CategoryBadge, formatDate } from '../components/Badges'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<{ status: Ticket['status']; resolution_notes: string }>({ status: 'open', resolution_notes: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    ticketApi.get(Number(id))
      .then((r) => {
        setTicket(r.data)
        setForm({ status: r.data.status, resolution_notes: r.data.resolution_notes ?? '' })
      })
      .catch(() => toast.error('Ticket not found'))
  }, [id])

  async function handleSave() {
    if (!ticket) return
    setLoading(true)
    try {
      const r = await ticketApi.update(ticket.id, form)
      setTicket(r.data)
      setEditing(false)
      toast.success('Ticket updated')
    } catch {
      toast.error('Update failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!ticket || !confirm('Delete this ticket permanently?')) return
    await ticketApi.delete(ticket.id)
    toast.success('Ticket deleted')
    navigate('/tickets')
  }

  if (!ticket) return <div className="text-gray-400 text-center py-20">Loading…</div>

  return (
    <div className="max-w-3xl mx-auto">
      <button onClick={() => navigate('/tickets')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-6">
        <ArrowLeft size={16} /> Back to tickets
      </button>

      <div className="card p-6 mb-4">
        <div className="flex items-start justify-between gap-4 mb-4">
          <h1 className="text-xl font-bold text-gray-900">{ticket.title}</h1>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => setEditing(!editing)} className="btn-secondary">
              {editing ? 'Cancel' : 'Edit'}
            </button>
            <button onClick={handleDelete} className="btn-danger">
              <Trash2 size={15} />
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-5">
          <CategoryBadge category={ticket.category} />
          <StatusBadge status={ticket.status} />
          <PriorityBadge priority={ticket.priority} />
          {ticket.ai_category_confidence !== null && (
            <span className="badge bg-gray-100 text-gray-600">
              AI confidence: {(ticket.ai_category_confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>

        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{ticket.description}</p>

        <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400 flex gap-6">
          <span>Created: {formatDate(ticket.created_at)}</span>
          <span>Updated: {formatDate(ticket.updated_at)}</span>
        </div>
      </div>

      {/* Edit Panel */}
      {editing && (
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-gray-900">Update Ticket</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select className="input w-48" value={form.status} onChange={(e) => setForm(f => ({ ...f, status: e.target.value as Ticket['status'] }))}>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resolution Notes</label>
            <textarea
              className="input resize-none"
              rows={4}
              value={form.resolution_notes}
              onChange={(e) => setForm(f => ({ ...f, resolution_notes: e.target.value }))}
              placeholder="Describe the resolution…"
            />
          </div>
          <button className="btn-primary" onClick={handleSave} disabled={loading}>
            <Save size={15} /> {loading ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      )}

      {/* Resolution notes (read-only) */}
      {!editing && ticket.resolution_notes && (
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-2">Resolution Notes</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{ticket.resolution_notes}</p>
        </div>
      )}
    </div>
  )
}
