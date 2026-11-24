/**
 * Auth context — stores token and user, provides login/logout helpers.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { User } from '../services/api'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('orbit_token'))
  const [user, setUser] = useState<User | null>(() => {
    const u = localStorage.getItem('orbit_user')
    return u ? JSON.parse(u) : null
  })

  const login = useCallback((newToken: string, newUser: User) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem('orbit_token', newToken)
    localStorage.setItem('orbit_user', JSON.stringify(newUser))
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('orbit_token')
    localStorage.removeItem('orbit_user')
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
