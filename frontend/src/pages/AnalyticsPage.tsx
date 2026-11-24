import { useEffect, useState } from 'react'
import { analyticsApi } from '../services/api'
import type { SystemStats } from '../services/api'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import toast from 'react-hot-toast'

const COLORS = ['#4f6ef7', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#6b7280']

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-6">
      <h2 className="font-semibold text-gray-900 mb-5">{title}</h2>
      {children}
    </div>
  )
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [faiss, setFaiss] = useState<{ total_indexed_vectors: number; index_dimension: number } | null>(null)

  useEffect(() => {
    analyticsApi.stats().then((r) => setStats(r.data)).catch(() => toast.error('Failed to load stats'))
    analyticsApi.faissInfo().then((r) => setFaiss(r.data)).catch(() => {})
  }, [])

  if (!stats) return <div className="text-gray-400 text-center py-20">Loading analytics…</div>

  const statusData = Object.entries(stats.tickets.by_status).map(([name, value]) => ({ name, value }))
  const categoryData = Object.entries(stats.tickets.by_category).map(([name, value]) => ({ name, value }))
  const priorityData = Object.entries(stats.tickets.by_priority).map(([name, value]) => ({ name, value }))

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analytics & Reports</h1>

      {/* Summary row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Tickets', value: stats.total_tickets },
          { label: 'Total Documents', value: stats.total_documents },
          { label: 'Indexed Chunks', value: stats.total_chunks },
          { label: 'FAISS Vectors', value: faiss?.total_indexed_vectors ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className="card p-5 text-center">
            <p className="text-3xl font-bold text-orbit-600">{value}</p>
            <p className="text-sm text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Ticket status */}
        <Section title="Tickets by Status">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={statusData} margin={{ left: -20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#4f6ef7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* Ticket category */}
        <Section title="Tickets by Category">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={categoryData.filter((d) => d.value > 0)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {categoryData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>

      {/* Priority breakdown */}
      <Section title="Tickets by Priority">
        <div className="grid grid-cols-4 gap-4">
          {priorityData.map(({ name, value }, i) => (
            <div key={name} className="text-center p-4 rounded-lg bg-gray-50">
              <div
                className="w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-bold"
                style={{ backgroundColor: COLORS[i] }}
              >
                {value}
              </div>
              <p className="text-sm text-gray-600 capitalize">{name}</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  )
}
