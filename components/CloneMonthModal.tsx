'use client'

import React, { useState } from 'react'
import { X, Copy, ArrowRight, Check } from 'lucide-react'
import { monthLabel, shiftMonth, type ThemeTokens } from '@/lib/theme'
import type { UIExpense } from './GastosApp'

interface CloneMonthModalProps {
  T: ThemeTokens
  currentMonthRef: string
  allExpenses: UIExpense[]
  onClose: () => void
  onClone: (fromMonth: string, toMonth: string) => Promise<void>
}

export function CloneMonthModal({
  T,
  currentMonthRef,
  allExpenses,
  onClose,
  onClone,
}: CloneMonthModalProps) {
  const [fromMonth, setFromMonth] = useState<string>(currentMonthRef)
  const [toMonth, setToMonth] = useState<string>(() => shiftMonth(currentMonthRef, 1))
  const [isCloning, setIsCloning] = useState(false)

  // Gerar lista de meses para os seletores (-12 meses até +12 meses em relação ao atual)
  const monthOptions = React.useMemo(() => {
    const options: string[] = []
    for (let i = -12; i <= 12; i++) {
      options.push(shiftMonth(currentMonthRef, i))
    }
    return Array.from(new Set(options)).sort()
  }, [currentMonthRef])

  // Contagem de lançamentos no mês de origem
  const sourceExpensesCount = React.useMemo(() => {
    return allExpenses.filter((e) => e.monthRef === fromMonth).length
  }, [allExpenses, fromMonth])

  // Contagem de lançamentos no mês de destino
  const targetExpensesCount = React.useMemo(() => {
    return allExpenses.filter((e) => e.monthRef === toMonth).length
  }, [allExpenses, toMonth])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (fromMonth === toMonth) return
    setIsCloning(true)
    try {
      await onClone(fromMonth, toMonth)
      onClose()
    } catch (err) {
      console.error('Erro ao clonar mês:', err)
    } finally {
      setIsCloning(false)
    }
  }

  const isSameMonth = fromMonth === toMonth

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-md rounded-2xl border p-6 shadow-2xl relative animate-in zoom-in-95 duration-200"
        style={{ backgroundColor: T.surfaceSolid, borderColor: T.border, color: T.textPrimary }}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b" style={{ borderColor: T.borderSubtle }}>
          <div className="flex items-center gap-2.5">
            <div
              className="p-2 rounded-xl"
              style={{ backgroundColor: `${T.accent}15`, color: T.accent }}
            >
              <Copy size={20} strokeWidth={2.2} />
            </div>
            <div>
              <h3 className="font-display font-semibold text-lg leading-tight">Clonar despesas de um mês</h3>
              <p className="text-xs mt-0.5" style={{ color: T.textFaint }}>
                Copie os lançamentos e recrie como pendentes
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border hover:opacity-80 transition-opacity"
            style={{ borderColor: T.borderSubtle, color: T.textMuted }}
          >
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Seleção De -> Para */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 bg-opacity-50 p-3 rounded-xl border" style={{ backgroundColor: T.inputBg, borderColor: T.borderSubtle }}>
            {/* Origem */}
            <div>
              <label className="block text-[10px] uppercase font-semibold font-mono mb-1" style={{ color: T.textFaint }}>
                Copiar de:
              </label>
              <select
                value={fromMonth}
                onChange={(e) => setFromMonth(e.target.value)}
                className="w-full text-xs font-medium rounded-lg px-2.5 py-2 border outline-none cursor-pointer"
                style={{ backgroundColor: T.surfaceSolid, borderColor: T.border, color: T.textPrimary }}
              >
                {monthOptions.map((m) => (
                  <option key={m} value={m}>
                    {monthLabel(m)}
                  </option>
                ))}
              </select>
              <span className="block text-[11px] font-mono mt-1" style={{ color: sourceExpensesCount > 0 ? T.accent : T.textFaint }}>
                {sourceExpensesCount} {sourceExpensesCount === 1 ? 'item' : 'itens'}
              </span>
            </div>

            {/* Seta explicativa */}
            <div className="pt-4 flex items-center justify-center text-muted" style={{ color: T.textFaint }}>
              <ArrowRight size={16} />
            </div>

            {/* Destino */}
            <div>
              <label className="block text-[10px] uppercase font-semibold font-mono mb-1" style={{ color: T.textFaint }}>
                Para o mês:
              </label>
              <select
                value={toMonth}
                onChange={(e) => setToMonth(e.target.value)}
                className="w-full text-xs font-medium rounded-lg px-2.5 py-2 border outline-none cursor-pointer"
                style={{ backgroundColor: T.surfaceSolid, borderColor: T.border, color: T.textPrimary }}
              >
                {monthOptions.map((m) => (
                  <option key={m} value={m}>
                    {monthLabel(m)}
                  </option>
                ))}
              </select>
              <span className="block text-[11px] font-mono mt-1" style={{ color: T.textFaint }}>
                {targetExpensesCount > 0 ? `Já possui ${targetExpensesCount} itens` : 'Mês vazio'}
              </span>
            </div>
          </div>

          {/* Alertas explicativos */}
          {isSameMonth && (
            <p className="text-xs p-2.5 rounded-lg border font-medium" style={{ backgroundColor: `${T.danger}15`, borderColor: `${T.danger}40`, color: T.danger }}>
              O mês de origem e de destino precisam ser diferentes.
            </p>
          )}

          {sourceExpensesCount === 0 && !isSameMonth && (
            <p className="text-xs p-2.5 rounded-lg border font-medium" style={{ backgroundColor: `${T.warning}15`, borderColor: `${T.warning}40`, color: T.warning }}>
              O mês selecionado ({monthLabel(fromMonth)}) não possui lançamentos para clonar.
            </p>
          )}

          {!isSameMonth && sourceExpensesCount > 0 && (
            <div className="text-xs p-3 rounded-xl border space-y-1 leading-relaxed" style={{ backgroundColor: `${T.accent}10`, borderColor: `${T.accent}30`, color: T.textMuted }}>
              <p style={{ color: T.textPrimary }}>
                <strong>{sourceExpensesCount}</strong> {sourceExpensesCount === 1 ? 'despesa será copiada' : 'despesas serão copiadas'} para <strong>{monthLabel(toMonth)}</strong>.
              </p>
              <p className="text-[11px]" style={{ color: T.textFaint }}>
                • Todas as despesas clonadas serão criadas com status <strong>Pendente</strong> e data de pagamento em branco.
              </p>
            </div>
          )}

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium border transition-all hover:opacity-80"
              style={{ backgroundColor: 'transparent', borderColor: T.border, color: T.textMuted }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isCloning || isSameMonth || sourceExpensesCount === 0}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              style={{ background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`, color: T.accentOnBrand }}
            >
              {isCloning ? (
                'Clonando...'
              ) : (
                <>
                  <Check size={14} strokeWidth={2.5} /> Clonar agora
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
