import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ticketApi } from '../services/api'
import toast from 'react-hot-toast'
import { ArrowLeft } from 'lucide-react'

export default function NewTicketPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'medium',
  })
  const [loading, setLoading] = useState(false)

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await ticketApi.create(form)
      toast.success('Ticket created and auto-classified!')
      navigate(`/tickets/${data.id}`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Failed to create ticket')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => navigate('/tickets')}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} /> Back to tickets
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Support Ticket</h1>

      <div className="card p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className="input"
              placeholder="Brief summary of the issue"
              value={form.title}
              onChange={(e) => update('title', e.target.value)}
              required
              minLength={5}
            />
            <p className="text-xs text-gray-400 mt-1">The AI will automatically categorize your ticket.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              className="input resize-none"
              rows={6}
              placeholder="Describe the issue in detail…"
              value={form.description}
              onChange={(e) => update('description', e.target.value)}
              required
              minLength={10}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              className="input w-48"
              value={form.priority}
              onChange={(e) => update('priority', e.target.value)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Submitting…' : 'Submit Ticket'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => navigate('/tickets')}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
