import { useEffect, useRef, useState } from 'react'
import { documentApi } from '../services/api'
import type { Document } from '../services/api'
import { formatDate, formatBytes } from '../components/Badges'
import { Upload, FileText, Trash2, CheckCircle, Loader } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const fileRef = useRef<HTMLInputElement>(null)

  async function load() {
    try {
      const r = await documentApi.list()
      setDocs(r.data)
    } catch {
      toast.error('Failed to load documents')
    }
  }

  useEffect(() => { load() }, [])

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.endsWith('.pdf')) {
      toast.error('Only PDF files are supported')
      return
    }
    setUploading(true)
    setProgress(0)
    try {
      await documentApi.upload(file, setProgress)
      toast.success(`"${file.name}" indexed successfully!`)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Upload failed')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function handleDelete(doc: Document) {
    if (!confirm(`Delete "${doc.original_filename}"? This cannot be undone.`)) return
    try {
      await documentApi.delete(doc.id)
      toast.success('Document deleted')
      setDocs((d) => d.filter((x) => x.id !== doc.id))
    } catch {
      toast.error('Delete failed')
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Documents</h1>
          <p className="text-gray-500 text-sm mt-1">Upload PDFs to build your AI knowledge base.</p>
        </div>
        <label className={`btn-primary cursor-pointer ${uploading ? 'opacity-60 pointer-events-none' : ''}`}>
          <Upload size={16} />
          {uploading ? `Uploading… ${progress}%` : 'Upload PDF'}
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
        </label>
      </div>

      {/* Upload progress bar */}
      {uploading && (
        <div className="mb-5 card p-4">
          <div className="flex items-center gap-3 mb-2">
            <Loader size={16} className="animate-spin text-orbit-600" />
            <span className="text-sm font-medium text-gray-700">Processing PDF — extracting, chunking, and indexing…</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-orbit-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Document list */}
      {docs.length === 0 ? (
        <div className="card p-16 text-center">
          <FileText size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 font-medium">No documents uploaded yet</p>
          <p className="text-sm text-gray-400 mt-1">Upload a PDF to enable AI-powered Q&A.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {docs.map((doc) => (
            <div key={doc.id} className="card p-5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
                <FileText size={20} className="text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{doc.original_filename}</p>
                <div className="flex flex-wrap gap-4 mt-1 text-xs text-gray-500">
                  <span>{formatBytes(doc.file_size)}</span>
                  <span>{doc.page_count} pages</span>
                  <span>{doc.chunk_count} chunks</span>
                  <span>Uploaded {formatDate(doc.created_at)}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {doc.is_indexed && (
                  <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                    <CheckCircle size={14} /> Indexed
                  </span>
                )}
                <button
                  onClick={() => handleDelete(doc)}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
