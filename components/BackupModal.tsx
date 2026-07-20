'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { X, Database, Plus, RefreshCw, AlertTriangle, CheckCircle2, Calendar, HardDrive } from 'lucide-react'
import { formatBRL, type ThemeTokens } from '@/lib/theme'
import { fetchBackups, createBackup, restoreBackup } from '@/lib/supabaseClient'
import type { BackupRecord } from '@/lib/types'

interface BackupModalProps {
  T: ThemeTokens
  onClose: () => void
  onRestored: () => Promise<void>
}

export function BackupModal({ T, onClose, onRestored }: BackupModalProps) {
  const [backups, setBackups] = useState<BackupRecord[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [creating, setCreating] = useState<boolean>(false)
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const loadBackups = useCallback(async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const list = await fetchBackups()
      setBackups(list)
    } catch (err) {
      console.error('Erro ao carregar lista de backups:', err)
      setErrorMsg('Não foi possível carregar o histórico de backups.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBackups()
  }, [loadBackups])

  const handleCreateManualBackup = async () => {
    setCreating(true)
    setErrorMsg(null)
    try {
      await createBackup('manual')
      await loadBackups()
    } catch (err) {
      console.error('Erro ao criar backup manual:', err)
      setErrorMsg('Falha ao gerar o backup manual.')
    } finally {
      setCreating(false)
    }
  }

  const handleConfirmRestore = async (id: string) => {
    setRestoringId(id)
    setErrorMsg(null)
    try {
      await restoreBackup(id)
      await onRestored()
      setConfirmId(null)
      onClose()
    } catch (err) {
      console.error('Erro ao restaurar backup:', err)
      setErrorMsg('Falha ao restaurar o backup selecionado.')
    } finally {
      setRestoringId(null)
    }
  }

  const formatDateLabel = (isoStr: string) => {
    try {
      const d = new Date(isoStr)
      return d.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoStr
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl rounded-3xl border shadow-2xl overflow-hidden flex flex-col max-h-[85vh] transition-all duration-300"
        style={{
          backgroundColor: T.surface,
          borderColor: T.border,
          color: T.textPrimary,
        }}
      >
        {/* Header do Modal */}
        <div className="p-5 md:p-6 border-b flex items-center justify-between" style={{ borderColor: T.border }}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-2xl flex items-center justify-center"
              style={{ backgroundColor: `${T.accent}20`, color: T.accent }}
            >
              <Database size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight font-display">Backups & Restauração</h2>
              <p className="text-xs" style={{ color: T.textFaint }}>
                Snapshots completos do banco de dados (Categorias e Despesas)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl transition-colors hover:opacity-80 cursor-pointer"
            style={{ color: T.textFaint }}
            aria-label="Fechar modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Banner Informativo de Automação */}
        <div
          className="px-6 py-3 border-b flex items-center justify-between gap-3 text-xs"
          style={{ backgroundColor: T.rowHover, borderColor: T.border }}
        >
          <div className="flex items-center gap-2" style={{ color: T.textMuted }}>
            <Calendar size={14} className="text-emerald-500 flex-shrink-0" />
            <span>Backup automático nos dias <strong>01</strong> e <strong>15</strong> • Retenção dos <strong>3 mais recentes</strong>.</span>
          </div>
          <button
            onClick={handleCreateManualBackup}
            disabled={creating}
            className="px-3 py-1.5 rounded-xl font-medium text-xs border transition-all cursor-pointer flex items-center gap-1.5 active:scale-95 flex-shrink-0"
            style={{
              backgroundColor: `${T.accent}15`,
              borderColor: `${T.accent}40`,
              color: T.accent,
            }}
          >
            {creating ? (
              <RefreshCw size={13} className="animate-spin" />
            ) : (
              <Plus size={13} />
            )}
            <span>Novo backup manual</span>
          </button>
        </div>

        {/* Mensagem de Erro se houver */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl border flex items-center gap-2 text-xs bg-red-500/10 border-red-500/30 text-red-400">
            <AlertTriangle size={15} className="flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Lista de Backups */}
        <div className="p-6 overflow-y-auto flex-1 space-y-3">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3" style={{ color: T.textFaint }}>
              <RefreshCw size={24} className="animate-spin" />
              <p className="text-xs">Carregando snapshots...</p>
            </div>
          ) : backups.length === 0 ? (
            <div
              className="py-12 px-4 rounded-2xl border border-dashed text-center flex flex-col items-center justify-center gap-2"
              style={{ borderColor: T.border, color: T.textFaint }}
            >
              <HardDrive size={32} strokeWidth={1.5} />
              <p className="text-sm font-medium">Nenhum backup encontrado</p>
              <p className="text-xs max-w-xs">
                Clique em &quot;Novo backup manual&quot; acima para registrar seu primeiro ponto de restauração agora.
              </p>
            </div>
          ) : (
            backups.map((bk) => {
              const isConfirming = confirmId === bk.id
              const isRestoring = restoringId === bk.id

              return (
                <div
                  key={bk.id}
                  className="p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  style={{
                    backgroundColor: isConfirming ? `${T.warning}0F` : T.surface,
                    borderColor: isConfirming ? `${T.warning}66` : T.border,
                  }}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-medium text-sm" style={{ color: T.textPrimary }}>
                        {formatDateLabel(bk.created_at)}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider ${
                          bk.type === 'automatico'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        }`}
                      >
                        {bk.type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs" style={{ color: T.textFaint }}>
                      <span>{bk.expenses_count} despesas</span>
                      <span>•</span>
                      <span>{bk.categories_count} categorias</span>
                      <span>•</span>
                      <span className="font-mono font-medium" style={{ color: T.accent }}>
                        {formatBRL(bk.total_amount)}
                      </span>
                    </div>
                  </div>

                  {/* Ações de Restauração */}
                  <div className="flex items-center gap-2 self-end sm:self-center">
                    {isConfirming ? (
                      <div className="flex items-center gap-2 animate-in fade-in duration-150">
                        <span className="text-xs font-medium" style={{ color: T.warning }}>
                          Substituir dados atuais?
                        </span>
                        <button
                          onClick={() => handleConfirmRestore(bk.id)}
                          disabled={isRestoring}
                          className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500 text-black hover:bg-amber-400 transition-all flex items-center gap-1 cursor-pointer active:scale-95"
                        >
                          {isRestoring ? (
                            <RefreshCw size={13} className="animate-spin" />
                          ) : (
                            <CheckCircle2 size={13} />
                          )}
                          <span>Confirmar</span>
                        </button>
                        <button
                          onClick={() => setConfirmId(null)}
                          disabled={isRestoring}
                          className="px-2.5 py-1.5 rounded-xl text-xs font-medium border cursor-pointer hover:opacity-80"
                          style={{ borderColor: T.border, color: T.textFaint }}
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmId(bk.id)}
                        className="px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer flex items-center gap-1.5 active:scale-95"
                        style={{
                          backgroundColor: `${T.surface}`,
                          borderColor: T.border,
                          color: T.textPrimary,
                        }}
                      >
                        <RefreshCw size={13} />
                        <span>Restaurar</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
