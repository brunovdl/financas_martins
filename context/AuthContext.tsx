'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

export interface User {
  id: string
  name: string
  email: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  expiresAt: number | null
  login: (credentials: { email: string; password: string }) => Promise<{ success: boolean; error?: string }>
  register: (data: { name: string; email: string; password: string }) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [expiresAt, setExpiresAt] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch('/api/auth/me')
      if (res.ok) {
        const data = await res.json()
        if (data.authenticated && data.user) {
          setUser(data.user)
          setExpiresAt(data.expiresAt)
        } else {
          setUser(null)
          setExpiresAt(null)
        }
      } else {
        setUser(null)
        setExpiresAt(null)
      }
    } catch (error) {
      console.error('Auth check error:', error)
      setUser(null)
      setExpiresAt(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Automatic 24-hour expiration monitor
  useEffect(() => {
    if (!expiresAt) return

    const timeRemaining = expiresAt - Date.now()
    if (timeRemaining <= 0) {
      logout()
      return
    }

    const timer = setTimeout(() => {
      alert('Sua sessão de 24 horas expirou. Por favor, faça login novamente.')
      logout()
    }, timeRemaining)

    return () => clearTimeout(timer)
  }, [expiresAt])

  const login = async (credentials: { email: string; password: string }) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      })
      const data = await res.json()

      if (!res.ok) {
        return { success: false, error: data.error || 'Falha ao realizar login.' }
      }

      setUser(data.user)
      setExpiresAt(data.expiresAt)
      return { success: true }
    } catch (err) {
      console.error('Login error:', err)
      return { success: false, error: 'Erro de conexão com o servidor.' }
    }
  }

  const register = async (formData: { name: string; email: string; password: string }) => {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      const data = await res.json()

      if (!res.ok) {
        return { success: false, error: data.error || 'Falha ao criar conta.' }
      }

      setUser(data.user)
      setExpiresAt(data.expiresAt)
      return { success: true }
    } catch (err) {
      console.error('Register error:', err)
      return { success: false, error: 'Erro de conexão com o servidor.' }
    }
  }

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' })
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setUser(null)
      setExpiresAt(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        expiresAt,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
}
