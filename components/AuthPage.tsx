'use client'

import React, { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import {
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  TrendingUp,
} from 'lucide-react'

export function AuthPage() {
  const { login, register } = useAuth()
  const [tab, setTab] = useState<'login' | 'register'>('login')

  // Form states
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Status states
  const [errorMsg, setErrorMsg] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Validation rules
  const isEmailValid = email.includes('@') && email.includes('.')
  const isPasswordMinLength = password.length >= 8
  const isNameValid = name.trim().length > 0

  const handleTabChange = (newTab: 'login' | 'register') => {
    setTab(newTab)
    setErrorMsg('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')

    if (!isEmailValid) {
      setErrorMsg('Por favor, informe um e-mail válido.')
      return
    }

    if (!isPasswordMinLength) {
      setErrorMsg('A senha deve conter no mínimo 8 caracteres.')
      return
    }

    if (tab === 'register' && !isNameValid) {
      setErrorMsg('Por favor, insira o seu nome de usuário.')
      return
    }

    setIsSubmitting(true)

    try {
      if (tab === 'login') {
        const res = await login({ email, password })
        if (!res.success) {
          setErrorMsg(res.error || 'Falha ao autenticar.')
        }
      } else {
        const res = await register({ name, email, password })
        if (!res.success) {
          setErrorMsg(res.error || 'Falha ao criar conta.')
        }
      }
    } catch (err) {
      setErrorMsg('Ocorreu um erro inesperado. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-[#070A12] text-slate-100 flex items-center justify-center p-4 relative overflow-hidden font-sans">
      {/* Dynamic Ambient Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-emerald-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-amber-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[160px] pointer-events-none" />

      {/* Main Glassmorphism Card */}
      <div className="w-full max-w-md bg-[#0F172A]/70 backdrop-blur-2xl border border-emerald-500/20 rounded-3xl p-8 shadow-2xl shadow-emerald-950/40 relative z-10">
        
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-500 to-amber-400 p-[1px] mb-4 shadow-lg shadow-emerald-500/20">
            <div className="w-full h-full bg-[#0B1120] rounded-[15px] flex items-center justify-center">
              <TrendingUp className="w-7 h-7 text-emerald-400" />
            </div>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
            MAI Finance
          </h1>
          <p className="text-sm text-slate-400 mt-1 font-medium">
            Gestão Financeira Inteligente & Protegida
          </p>
        </div>

        {/* Integrated Tab Switcher */}
        <div className="flex bg-[#0B1120]/80 p-1.5 rounded-2xl border border-slate-800 mb-6">
          <button
            type="button"
            onClick={() => handleTabChange('login')}
            className={`flex-1 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 ${
              tab === 'login'
                ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Entrar
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('register')}
            className={`flex-1 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 ${
              tab === 'register'
                ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Criar Conta
          </button>
        </div>

        {/* Error Alert Box */}
        {errorMsg && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center gap-3 text-red-400 text-sm animate-shake">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Container */}
        <form onSubmit={handleSubmit} className="space-y-4">

          {/* Name Field (Only on Register) */}
          {tab === 'register' && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider pl-1">
                Nome de usuário
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  required
                  placeholder="Seu nome ou apelido"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#0B1120]/90 border border-slate-700/70 focus:border-emerald-500/80 focus:ring-2 focus:ring-emerald-500/20 text-white placeholder-slate-500 text-sm rounded-2xl pl-12 pr-4 py-3.5 outline-none transition-all"
                />
              </div>
            </div>
          )}

          {/* Email Field */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider pl-1">
              Endereço de E-mail
            </label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="email"
                required
                placeholder="seu.email@exemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#0B1120]/90 border border-slate-700/70 focus:border-emerald-500/80 focus:ring-2 focus:ring-emerald-500/20 text-white placeholder-slate-500 text-sm rounded-2xl pl-12 pr-4 py-3.5 outline-none transition-all"
              />
            </div>
          </div>

          {/* Password Field */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider pl-1">
              Senha (Mínimo 8 caracteres)
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={8}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0B1120]/90 border border-slate-700/70 focus:border-emerald-500/80 focus:ring-2 focus:ring-emerald-500/20 text-white placeholder-slate-500 text-sm rounded-2xl pl-12 pr-12 py-3.5 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            {/* Real-time Password Strength Meter */}
            {password.length > 0 && (
              <div className="pt-1.5 space-y-1">
                <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
                  <span>Requisito de Senha:</span>
                  <span className={isPasswordMinLength ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                    {password.length}/8 caracteres
                  </span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      password.length >= 12
                        ? 'w-full bg-emerald-400'
                        : isPasswordMinLength
                        ? 'w-3/4 bg-emerald-500'
                        : 'w-1/4 bg-amber-500'
                    }`}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-6 py-4 px-6 bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-sm rounded-2xl shadow-lg shadow-emerald-600/30 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>{tab === 'login' ? 'Acessar Conta' : 'Concluir Cadastro'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* 24-Hour Session Security Footer */}
        <div className="mt-8 pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Sessão ativa por <strong>24 horas</strong></span>
          </div>
          <div className="flex items-center gap-1 text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>JWT Protegido</span>
          </div>
        </div>

      </div>
    </div>
  )
}
