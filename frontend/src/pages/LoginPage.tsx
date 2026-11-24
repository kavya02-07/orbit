import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authApi.login(email, password)
      login(data.access_token, data.user)
      toast.success(`Welcome back, ${data.user.full_name}!`)
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orbit-50 to-blue-50 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-orbit-600 rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">O</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome to Orbit</h1>
          <p className="text-gray-500 mt-1">AI-Powered Support Assistant</p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-5">
            No account?{' '}
            <Link to="/register" className="text-orbit-600 hover:underline font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
