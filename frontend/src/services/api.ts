/**
 * Orbit API client — axios instance with JWT auth and error handling.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('orbit_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401 — clear token and reload
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('orbit_token')
      localStorage.removeItem('orbit_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Ticket {
  id: number
  title: string
  description: string
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  category: 'account' | 'billing' | 'technical' | 'cancellation' | 'feature' | 'security' | 'uncategorized'
  ai_category_confidence: number | null
  resolution_notes: string | null
  owner_id: number
  created_at: string
  updated_at: string
}

export interface TicketListResponse {
  items: Ticket[]
  total: number
  page: number
  page_size: number
}

export interface Document {
  id: number
  filename: string
  original_filename: string
  file_size: number
  page_count: number
  chunk_count: number
  is_indexed: boolean
  owner_id: number
  created_at: string
}

export interface SourceReference {
  document_id: number
  document_name: string
  chunk_index: number
  page_number: number | null
  excerpt: string
  similarity_score: number
}

export interface AnswerResponse {
  question: string
  answer: string
  sources: SourceReference[]
  model_used: string
  has_sufficient_context: boolean
}

export interface TicketStats {
  total: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  by_priority: Record<string, number>
}

export interface SystemStats {
  total_users: number
  total_tickets: number
  total_documents: number
  total_chunks: number
  tickets: TicketStats
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, full_name: string, password: string) =>
    api.post<TokenResponse>('/auth/register', { email, full_name, password }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  me: () => api.get<User>('/auth/me'),
}

// ── Tickets ───────────────────────────────────────────────────────────────────

export const ticketApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; category?: string }) =>
    api.get<TicketListResponse>('/tickets/', { params }),

  create: (data: { title: string; description: string; priority: string }) =>
    api.post<Ticket>('/tickets/', data),

  get: (id: number) => api.get<Ticket>(`/tickets/${id}`),

  update: (id: number, data: Partial<Ticket>) =>
    api.patch<Ticket>(`/tickets/${id}`, data),

  delete: (id: number) => api.delete(`/tickets/${id}`),
}

// ── Documents ─────────────────────────────────────────────────────────────────

export const documentApi = {
  list: () => api.get<Document[]>('/documents/'),

  upload: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Document>('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) {
          onProgress(Math.round((evt.loaded / evt.total) * 100))
        }
      },
    })
  },

  delete: (id: number) => api.delete(`/documents/${id}`),
}

// ── Q&A ───────────────────────────────────────────────────────────────────────

export const qaApi = {
  ask: (question: string, top_k = 5) =>
    api.post<AnswerResponse>('/qa/ask', { question, top_k }),
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export const analyticsApi = {
  stats: () => api.get<SystemStats>('/analytics/stats'),
  faissInfo: () => api.get('/analytics/faiss-info'),
}

export default api
