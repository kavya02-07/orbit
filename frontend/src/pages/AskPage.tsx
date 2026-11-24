import { useState } from 'react'
import { qaApi } from '../services/api'
import type { AnswerResponse } from '../services/api'
import { Send, ChevronDown, ChevronUp, BookOpen, AlertCircle, CheckCircle } from 'lucide-react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

export default function AskPage() {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnswerResponse | null>(null)
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set())
  const [history, setHistory] = useState<AnswerResponse[]>([])

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await qaApi.ask(question, topK)
      setResult(data)
      setHistory((h) => [data, ...h.slice(0, 9)])
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Failed to get answer')
    } finally {
      setLoading(false)
    }
  }

  function toggleSource(idx: number) {
    setExpandedSources((s) => {
      const next = new Set(s)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ask the Knowledge Base</h1>
        <p className="text-gray-500 text-sm mt-1">
          Ask anything about your uploaded documents. Answers are grounded in retrieved content.
        </p>
      </div>

      {/* Question form */}
      <form onSubmit={handleAsk} className="card p-5 mb-6">
        <div className="flex gap-3">
          <textarea
            className="input flex-1 resize-none"
            rows={3}
            placeholder="What is the refund policy? How do I reset my password? …"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
            minLength={5}
          />
        </div>
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <label>Top-K sources:</label>
            <select
              className="input w-16 py-1"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
            >
              {[3, 5, 10].map((k) => <option key={k}>{k}</option>)}
            </select>
          </div>
          <button type="submit" className="btn-primary" disabled={loading || !question.trim()}>
            <Send size={16} />
            {loading ? 'Searching…' : 'Ask'}
          </button>
        </div>
      </form>

      {/* Answer */}
      {result && (
        <div className="card p-6 mb-6">
          <div className="flex items-start gap-3 mb-4">
            {result.has_sufficient_context ? (
              <CheckCircle size={20} className="text-green-500 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle size={20} className="text-yellow-500 mt-0.5 shrink-0" />
            )}
            <div>
              <p className="text-xs text-gray-400 mb-2">
                Model: {result.model_used} · {result.sources.length} source(s)
              </p>
              <p className="text-gray-900 whitespace-pre-wrap leading-relaxed">{result.answer}</p>
            </div>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="mt-4 border-t border-gray-100 pt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Source References
              </p>
              <div className="space-y-2">
                {result.sources.map((src, i) => (
                  <div key={i} className="rounded-lg border border-gray-200 overflow-hidden">
                    <button
                      onClick={() => toggleSource(i)}
                      className="w-full flex items-center justify-between px-4 py-2 text-left text-sm bg-gray-50 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <BookOpen size={14} className="text-orbit-600" />
                        <span className="font-medium text-gray-800">{src.document_name}</span>
                        {src.page_number && (
                          <span className="text-gray-400">· p. {src.page_number}</span>
                        )}
                        <span className="badge bg-orbit-50 text-orbit-700">
                          {(src.similarity_score * 100).toFixed(1)}% match
                        </span>
                      </div>
                      {expandedSources.has(i) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    {expandedSources.has(i) && (
                      <div className="px-4 py-3 bg-white text-sm text-gray-600 leading-relaxed border-t border-gray-100">
                        {src.excerpt}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* History */}
      {history.length > 1 && (
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Recent Questions</p>
          <div className="space-y-2">
            {history.slice(1).map((h, i) => (
              <button
                key={i}
                onClick={() => { setQuestion(h.question); setResult(h) }}
                className="w-full text-left card px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {h.question}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
