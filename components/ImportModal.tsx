'use client'

import React, { useState, useRef } from 'react'
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, ChevronDown, X } from 'lucide-react'
import { CATEGORIES, formatBRL, monthLabel, type ThemeTokens } from '@/lib/theme'
import type { NewExpense } from '@/lib/types'

export interface ParsedImportRow {
  id?: string
  monthRef: string
  dueDay: number
  category: string
  description: string
  amount: number
  paymentDay: string
  status: 'pago' | 'pendente'
  observation: string
  // Supabase compatible payload
  toNewExpense: () => NewExpense
}

interface ImportModalProps {
  T: ThemeTokens
  theme: 'dark' | 'light'
  monthRef: string
  onClose: () => void
  onImport: (rows: ParsedImportRow[]) => void
}

const IMPORT_FIELDS = [
  { key: 'due_date', label: 'Vencimento', required: true, hint: 'Data: 05, 5, 05/04/2026, 2026-04-05' },
  { key: 'description', label: 'Descrição', required: true, hint: 'Texto livre' },
  { key: 'amount', label: 'Valor', required: true, hint: 'Número: 1234.56 ou 1.234,56' },
  { key: 'category', label: 'Categoria', required: false, hint: 'Nome da categoria (Outros, DAAE…)' },
  { key: 'status', label: 'Status', required: false, hint: 'pago | pendente' },
  { key: 'payment_date', label: 'Data Pagamento', required: false, hint: 'Igual ao Vencimento' },
  { key: 'observation', label: 'Observação', required: false, hint: 'Texto livre' },
]

function parseAmount(raw: unknown): number {
  if (raw === null || raw === undefined || raw === '') return 0
  const s = String(raw).trim()
  const cleaned = s.replace(/R\$\s*/g, '').trim()
  if (/\d,\d{1,2}$/.test(cleaned)) {
    return parseFloat(cleaned.replace(/\./g, '').replace(',', '.')) || 0
  }
  return parseFloat(cleaned.replace(',', '.')) || 0
}

function parseDateField(raw: unknown, monthRef: string): number {
  if (!raw && raw !== 0) return 1
  const s = String(raw).trim()
  if (/^\d{1,2}$/.test(s)) {
    return parseInt(s, 10)
  }
  const dotMatch = s.match(/^(\d{1,2})\..+/)
  if (dotMatch) return parseInt(dotMatch[1], 10)
  const brMatch = s.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})/)
  if (brMatch) return parseInt(brMatch[1], 10)
  const isoMatch = s.match(/(\d{4})-(\d{2})-(\d{2})/)
  if (isoMatch) return parseInt(isoMatch[3], 10)
  const num = parseFloat(s)
  if (!isNaN(num) && num > 40000) {
    const d = new Date(Math.round((num - 25569) * 86400 * 1000))
    return d.getDate()
  }
  return 1
}

function parseCategory(raw: unknown): string {
  if (!raw) return 'outros'
  const name = String(raw).trim().toLowerCase()
  const found = CATEGORIES.find((c) => c.name.toLowerCase() === name || c.id === name)
  return found ? found.id : 'outros'
}

function parseStatus(raw: unknown): 'pago' | 'pendente' {
  if (!raw) return 'pendente'
  const s = String(raw).trim().toLowerCase()
  return s === 'pago' || s === 'paid' ? 'pago' : 'pendente'
}

export function ImportModal({ T, theme, monthRef, onClose, onImport }: ImportModalProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState<'upload' | 'map' | 'preview'>('upload')
  const [headers, setHeaders] = useState<string[]>([])
  const [rows, setRows] = useState<unknown[][]>([])
  const [mapping, setMapping] = useState<Record<string, number>>({})
  const [preview, setPreview] = useState<ParsedImportRow[]>([])
  const [error, setError] = useState('')
  const [isDragging, setIsDragging] = useState(false)

  async function loadSheetJS() {
    if ((window as unknown as { XLSX?: unknown }).XLSX) {
      return (window as unknown as { XLSX: unknown }).XLSX
    }
    return new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js'
      s.onload = () => resolve((window as unknown as { XLSX: unknown }).XLSX)
      s.onerror = () => reject(new Error('Falha ao carregar SheetJS'))
      document.head.appendChild(s)
    })
  }

  async function handleFile(file?: File) {
    setError('')
    if (!file) return
    const isCSV = file.name.endsWith('.csv')
    const isXLSX = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
    if (!isCSV && !isXLSX) {
      setError('Formato não suportado. Use .xlsx, .xls ou .csv')
      return
    }
    try {
      const XLSX = (await loadSheetJS()) as {
        read: (buf: ArrayBuffer, opts: { type: string }) => { Sheets: Record<string, unknown>; SheetNames: string[] }
        utils: { sheet_to_json: (ws: unknown, opts: { header: number; defval: string }) => unknown[][] }
      }
      const buf = await file.arrayBuffer()
      const wb = XLSX.read(buf, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
      if (data.length < 2) {
        setError('Arquivo vazio ou sem dados.')
        return
      }
      const hdrs = data[0].map((h) => String(h).trim())
      const dataRows = data.slice(1).filter((r) => r.some((c) => c !== ''))
      setHeaders(hdrs)
      setRows(dataRows)

      const autoMap: Record<string, number> = {}
      const aliases: Record<string, string[]> = {
        due_date: ['vencimento', 'due_date', 'due date', 'data vencimento', 'data'],
        description: ['descricao', 'descrição', 'description', 'desc', 'nome'],
        amount: ['valor', 'amount', 'value', 'vlr'],
        category: ['categoria', 'category', 'cat'],
        status: ['status', 'situacao', 'situação'],
        payment_date: ['pagamento', 'data pagamento', 'payment_date', 'payment date', 'pago em'],
        observation: ['observacao', 'observação', 'observation', 'obs', 'nota'],
      }

      hdrs.forEach((h, i) => {
        const lower = h.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        for (const [field, list] of Object.entries(aliases)) {
          if (list.some((a) => lower.includes(a))) {
            if (autoMap[field] === undefined) autoMap[field] = i
          }
        }
      })
      setMapping(autoMap)
      setStep('map')
    } catch (e) {
      setError('Erro ao ler arquivo: ' + (e as Error).message)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  function buildPreview() {
    let idC = Date.now()
    const built: ParsedImportRow[] = rows.slice(0, 200).map((row) => {
      const dueDay = parseDateField(mapping.due_date !== undefined ? row[mapping.due_date] : null, monthRef)
      const category = parseCategory(mapping.category !== undefined ? row[mapping.category] : '')
      const description = mapping.description !== undefined ? String(row[mapping.description] || '').trim() : '—'
      const amount = parseAmount(mapping.amount !== undefined ? row[mapping.amount] : 0)
      const paymentDay = mapping.payment_date !== undefined ? String(row[mapping.payment_date] || '').trim() : ''
      const status = parseStatus(mapping.status !== undefined ? row[mapping.status] : '')
      const observation = mapping.observation !== undefined ? String(row[mapping.observation] || '').trim() : ''

      const formattedDay = String(dueDay).padStart(2, '0')
      const dueDateIso = `${monthRef}-${formattedDay}`

      return {
        id: `imp-${idC++}`,
        monthRef,
        dueDay,
        category,
        description,
        amount,
        paymentDay,
        status,
        observation,
        toNewExpense: (): NewExpense => ({
          due_date: dueDateIso,
          category_id: null, // ser preenchido se houver ID de categoria
          description,
          amount,
          payment_date: paymentDay || null,
          status,
          observation: observation || null,
          month_ref: monthRef,
        }),
      }
    })
    setPreview(built)
    setStep('preview')
  }

  const requiredMapped = IMPORT_FIELDS.filter((f) => f.required).every((f) => mapping[f.key] !== undefined)

  const inputStyle = {
    backgroundColor: T.inputBg,
    borderColor: T.border,
    color: T.textPrimary,
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(6px)' }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="w-full max-w-2xl rounded-2xl border flex flex-col overflow-hidden"
        style={{ backgroundColor: T.surfaceSolid, borderColor: T.border, maxHeight: '90vh' }}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: T.border }}>
          <div className="flex items-center gap-2.5">
            <FileSpreadsheet size={18} style={{ color: T.accent }} />
            <span className="font-display font-semibold text-base" style={{ color: T.textPrimary }}>
              Importar Planilha
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono" style={{ backgroundColor: `${T.accent}20`, color: T.accent }}>
              {step === 'upload' ? '1/3' : step === 'map' ? '2/3' : '3/3'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: T.textFaint }}
            onMouseEnter={(e) => (e.currentTarget.style.color = T.danger)}
            onMouseLeave={(e) => (e.currentTarget.style.color = T.textFaint)}
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* STEP 1: Upload */}
          {step === 'upload' && (
            <div className="p-6">
              <p className="text-sm mb-5" style={{ color: T.textMuted }}>
                Faça upload de um arquivo <strong>.xlsx</strong>, <strong>.xls</strong> ou <strong>.csv</strong>. A primeira linha deve conter os nomes das colunas.
              </p>
              <div
                className="border-2 border-dashed rounded-2xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors"
                style={{ borderColor: isDragging ? T.accent : T.border, backgroundColor: isDragging ? `${T.accent}10` : 'transparent' }}
                onDragOver={(e) => {
                  e.preventDefault()
                  setIsDragging(true)
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={32} style={{ color: isDragging ? T.accent : T.textFaint }} />
                <p className="text-sm font-medium" style={{ color: isDragging ? T.accent : T.textMuted }}>
                  Arraste o arquivo aqui ou clique para selecionar
                </p>
                <p className="text-xs" style={{ color: T.textFaint }}>
                  .xlsx · .xls · .csv
                </p>
              </div>
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
              {error && (
                <div className="mt-4 flex items-center gap-2 text-sm px-3 py-2.5 rounded-lg" style={{ backgroundColor: `${T.danger}18`, color: T.danger }}>
                  <AlertCircle size={14} /> {error}
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Mapping */}
          {step === 'map' && (
            <div className="p-6">
              <p className="text-sm mb-1" style={{ color: T.textMuted }}>
                Arquivo carregado com <strong>{headers.length}</strong> colunas e <strong>{rows.length}</strong> linhas.
              </p>
              <p className="text-xs mb-5" style={{ color: T.textFaint }}>
                Associe cada campo abaixo a uma coluna da sua planilha. Campos marcados com * são obrigatórios.
              </p>

              <div className="flex flex-col gap-3">
                {IMPORT_FIELDS.map((field) => (
                  <div key={field.key} className="flex items-center gap-3">
                    <div className="w-36 flex-shrink-0">
                      <span className="text-sm font-medium" style={{ color: T.textPrimary }}>
                        {field.label}
                        {field.required && <span style={{ color: T.danger }}> *</span>}
                      </span>
                      <p className="text-[11px] mt-0.5" style={{ color: T.textFaint }}>
                        {field.hint}
                      </p>
                    </div>
                    <div className="relative flex-1">
                      <select
                        value={mapping[field.key] !== undefined ? mapping[field.key] : ''}
                        onChange={(e) => {
                          const val = e.target.value
                          setMapping((prev) => {
                            const next = { ...prev }
                            if (val === '') delete next[field.key]
                            else next[field.key] = parseInt(val, 10)
                            return next
                          })
                        }}
                        className="w-full text-sm border rounded-xl px-3 py-2 outline-none appearance-none cursor-pointer"
                        style={inputStyle}
                      >
                        <option value="">— não mapear —</option>
                        {headers.map((h, i) => (
                          <option key={i} value={i}>
                            {h} {rows[0]?.[i] !== undefined ? `(ex: ${String(rows[0][i]).slice(0, 20)})` : ''}
                          </option>
                        ))}
                      </select>
                      <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: T.textFaint }} />
                    </div>
                    {mapping[field.key] !== undefined ? (
                      <CheckCircle2 size={16} style={{ color: T.success }} />
                    ) : (
                      <div style={{ width: 16 }} />
                    )}
                  </div>
                ))}
              </div>

              {error && (
                <div className="mt-4 flex items-center gap-2 text-sm px-3 py-2.5 rounded-lg" style={{ backgroundColor: `${T.danger}18`, color: T.danger }}>
                  <AlertCircle size={14} /> {error}
                </div>
              )}
            </div>
          )}

          {/* STEP 3: Preview */}
          {step === 'preview' && (
            <div className="p-6">
              <p className="text-sm mb-4" style={{ color: T.textMuted }}>
                <strong>{preview.length}</strong> {preview.length === 1 ? 'registro' : 'registros'} prontos para importar no mês{' '}
                <strong>{monthLabel(monthRef)}</strong>. Confira antes de confirmar:
              </p>
              <div className="overflow-x-auto rounded-xl border" style={{ borderColor: T.border }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ backgroundColor: `${T.border}60`, color: T.textFaint }}>
                      {['Dia', 'Categoria', 'Descrição', 'Valor', 'Status'].map((h) => (
                        <th key={h} className="px-3 py-2 text-left font-medium">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.slice(0, 10).map((row, i) => {
                      const cat = CATEGORIES.find((c) => c.id === row.category)
                      const catColor = theme === 'dark' ? cat?.dark : cat?.light
                      const isPago = row.status === 'pago'
                      return (
                        <tr key={i} style={{ borderTop: `1px solid ${T.borderSubtle}` }}>
                          <td className="px-3 py-2 font-mono" style={{ color: T.textMuted }}>
                            {String(row.dueDay).padStart(2, '0')}
                          </td>
                          <td className="px-3 py-2">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ backgroundColor: `${catColor}20`, color: catColor }}>
                              {cat?.name}
                            </span>
                          </td>
                          <td className="px-3 py-2" style={{ color: T.textPrimary }}>
                            {row.description}
                          </td>
                          <td className="px-3 py-2 font-mono" style={{ color: T.textPrimary }}>
                            {formatBRL(row.amount)}
                          </td>
                          <td className="px-3 py-2">
                            <span
                              className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                              style={isPago ? { backgroundColor: `${T.success}1F`, color: T.successText } : { backgroundColor: `${T.warning}1F`, color: T.warning }}
                            >
                              {isPago ? 'Pago' : 'Pendente'}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              {preview.length > 10 && (
                <p className="text-xs mt-2 text-center" style={{ color: T.textFaint }}>
                  + {preview.length - 10} registros não exibidos
                </p>
              )}
            </div>
          )}
        </div>

        {/* Modal footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t" style={{ borderColor: T.border }}>
          <button
            onClick={() => (step === 'upload' ? onClose() : step === 'map' ? setStep('upload') : setStep('map'))}
            className="px-4 py-2 rounded-xl text-sm border transition-all"
            style={{ borderColor: T.border, color: T.textMuted, backgroundColor: 'transparent' }}
          >
            {step === 'upload' ? 'Cancelar' : '← Voltar'}
          </button>
          {step === 'map' && (
            <button
              onClick={requiredMapped ? buildPreview : undefined}
              className="px-5 py-2 rounded-xl text-sm font-semibold transition-all"
              style={{
                background: requiredMapped ? `linear-gradient(90deg, ${T.accent}, ${T.accentTo})` : T.border,
                color: requiredMapped ? T.accentOnBrand : T.textFaint,
                cursor: requiredMapped ? 'pointer' : 'not-allowed',
              }}
            >
              Visualizar prévia →
            </button>
          )}
          {step === 'preview' && (
            <button
              onClick={() => onImport(preview)}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98]"
              style={{ background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`, color: T.accentOnBrand }}
            >
              <CheckCircle2 size={15} /> Importar {preview.length} registros
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
