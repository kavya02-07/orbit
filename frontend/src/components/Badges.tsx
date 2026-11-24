import { clsx } from 'clsx'

// ── Badge helpers ─────────────────────────────────────────────────────────────

export const statusColors: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-700',
}

export const priorityColors: Record<string, string> = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-orange-100 text-orange-700',
  high: 'bg-red-100 text-red-700',
  critical: 'bg-red-200 text-red-900 font-bold',
}

export const categoryColors: Record<string, string> = {
  account: 'bg-purple-100 text-purple-800',
  billing: 'bg-green-100 text-green-800',
  technical: 'bg-orange-100 text-orange-800',
  cancellation: 'bg-red-100 text-red-800',
  feature: 'bg-blue-100 text-blue-800',
  security: 'bg-rose-100 text-rose-800',
  uncategorized: 'bg-gray-100 text-gray-700',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx('badge', statusColors[status] ?? 'bg-gray-100 text-gray-700')}>
      {status.replace('_', ' ')}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={clsx('badge', priorityColors[priority] ?? 'bg-gray-100 text-gray-700')}>
      {priority}
    </span>
  )
}

export function CategoryBadge({ category }: { category: string }) {
  return (
    <span className={clsx('badge', categoryColors[category] ?? 'bg-gray-100 text-gray-700')}>
      {category}
    </span>
  )
}

// ── Misc helpers ──────────────────────────────────────────────────────────────

export function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
