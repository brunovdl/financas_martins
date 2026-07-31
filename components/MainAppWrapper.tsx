'use client'

import React from 'react'
import { useAuth } from '@/context/AuthContext'
import { AuthPage } from './AuthPage'
import GastosApp from './GastosApp'
import { LogOut, User, ShieldCheck, Clock, TrendingUp } from 'lucide-react'

export function MainAppWrapper() {
  const { user, isAuthenticated, isLoading, expiresAt, logout } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-[#070A12] flex flex-col items-center justify-center text-slate-200">
        <div className="relative flex items-center justify-center mb-4">
          <div className="w-16 h-16 border-4 border-emerald-500/20 border-t-emerald-400 rounded-full animate-spin" />
          <TrendingUp className="w-6 h-6 text-emerald-400 absolute" />
        </div>
        <p className="text-sm font-medium text-slate-400">Verificando sessão de 24 horas...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <AuthPage />
  }

  // Session time remaining calculation
  const getSessionRemainingText = () => {
    if (!expiresAt) return 'Sessão ativa'
    const diff = expiresAt - Date.now()
    if (diff <= 0) return 'Expirado'
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours}h ${minutes}m restantes`
  }

  return (
    <div className="min-h-screen w-full flex flex-col bg-[#0F172A]">
      {/* Top User Bar */}
      <header className="w-full bg-[#0B1120] border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 font-bold text-xs shadow-md shadow-emerald-500/20">
            {user?.name?.slice(0, 2).toUpperCase() || 'US'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-100">{user?.name}</span>
              <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full font-semibold">
                <ShieldCheck className="w-3 h-3" />
                Sessão 24h
              </span>
            </div>
            <span className="text-xs text-slate-400">{user?.email}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>{getSessionRemainingText()}</span>
          </div>

          <button
            onClick={logout}
            title="Encerrar sessão"
            className="flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-red-400 bg-slate-800/60 hover:bg-red-500/10 border border-slate-700/60 hover:border-red-500/30 px-3 py-1.5 rounded-xl transition-all cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden xs:inline">Sair</span>
          </button>
        </div>
      </header>

      {/* Main Application */}
      <main className="flex-1">
        <GastosApp />
      </main>
    </div>
  )
}
