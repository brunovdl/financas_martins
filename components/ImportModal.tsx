'use client'

import React, { useState, useRef } from 'react'
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, ChevronDown, X } from 'lucide-react'
import { CATEGORIES, formatBRL, monthLabel, type ThemeTokens, type CategoryTheme } from '@/lib/theme'
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
  categoriesList?: CategoryTheme[]
  onClose: () => void
  onImport: (rows: ParsedImportRow[]) => void
}

const IMPORT_FIELDS = [
  { key: 'due_date', label: 'Vencimento', required: true, hint: 'Data: 05, 5, 05/04/2026, 2026-04-05' },
  { key: 'month_ref', label: 'Mês/Ano Ref', required: false, hint: 'ex: 04/2026, 2026-04, Abril/2026' },
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

const MONTH_NAMES: Record<string, string> = {
  janeiro: '01', jan: '01',
  fevereiro: '02', fev: '02',
  marco: '03', março: '03', mar: '03',
  abril: '04', abr: '04',
  maio: '05', mai: '05',
  junho: '06', jun: '06',
  julho: '07', jul: '07',
  agosto: '08', ago: '08',
  setembro: '09', set: '09',
  outubro: '10', out: '10',
  novembro: '11', nov: '11',
  dezembro: '12', dez: '12',
}

function parseMonthRef(raw: unknown): string | null {
  if (raw === null || raw === undefined || raw === '') return null
  const s = String(raw).trim()
  if (!s) return null

  // Format: YYYY-MM
  const isoMatch = s.match(/^(\d{4})[-/.](\d{1,2})$/)
  if (isoMatch) {
    const y = isoMatch[1]
    const m = String(parseInt(isoMatch[2], 10)).padStart(2, '0')
    if (parseInt(m, 10) >= 1 && parseInt(m, 10) <= 12) return `${y}-${m}`
  }

  // Format: MM/YYYY or MM-YYYY
  const brMatch = s.match(/^(\d{1,2})[-/.](\d{4})$/)
  if (brMatch) {
    const m = String(parseInt(brMatch[1], 10)).padStart(2, '0')
    const y = brMatch[2]
    if (parseInt(m, 10) >= 1 && parseInt(m, 10) <= 12) return `${y}-${m}`
  }

  // Format: "Abril/2026", "Abr 2026", "Abril 26"
  const textMatch = s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').match(/^([a-z]+)[\s/.-]*(\d{2,4})$/)
  if (textMatch) {
    const mName = textMatch[1]
    let year = textMatch[2]
    if (year.length === 2) year = `20${year}`
    const mCode = MONTH_NAMES[mName]
    if (mCode && year) return `${year}-${mCode}`
  }

  // Excel serial date check
  const num = parseFloat(s)
  if (!isNaN(num) && num > 40000 && num < 60000) {
    const d = new Date(Math.round((num - 25569) * 86400 * 1000))
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      return `${y}-${m}`
    }
  }

  return null
}

function parseDateField(raw: unknown, defaultMonthRef: string): { dueDay: number; monthRef: string } {
  if (raw === null || raw === undefined || raw === '') return { dueDay: 1, monthRef: defaultMonthRef }
  const s = String(raw).trim()
  if (!s) return { dueDay: 1, monthRef: defaultMonthRef }

  // Just day number: "5" or "05"
  if (/^\d{1,2}$/.test(s)) {
    const day = Math.min(31, Math.max(1, parseInt(s, 10) || 1))
    return { dueDay: day, monthRef: defaultMonthRef }
  }

  // "05/10" without year?
  const dayMonthOnly = s.match(/^(\d{1,2})[\/-](\d{1,2})$/)
  if (dayMonthOnly) {
    const day = Math.min(31, Math.max(1, parseInt(dayMonthOnly[1], 10) || 1))
    const m = String(parseInt(dayMonthOnly[2], 10)).padStart(2, '0')
    const currentYear = defaultMonthRef.slice(0, 4)
    if (parseInt(m, 10) >= 1 && parseInt(m, 10) <= 12) {
      return { dueDay: day, monthRef: `${currentYear}-${m}` }
    }
    return { dueDay: day, monthRef: defaultMonthRef }
  }

  // BR Full Date: DD/MM/YYYY or DD-MM-YYYY
  const brMatch = s.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})/)
  if (brMatch) {
    const day = Math.min(31, Math.max(1, parseInt(brMatch[1], 10) || 1))
    const m = String(parseInt(brMatch[2], 10)).padStart(2, '0')
    const y = brMatch[3]
    return { dueDay: day, monthRef: `${y}-${m}` }
  }

  // ISO Full Date: YYYY-MM-DD
  const isoMatch = s.match(/^(\d{4})[-/.](\d{2})[-/.](\d{2})/)
  if (isoMatch) {
    const y = isoMatch[1]
    const m = isoMatch[2]
    const day = Math.min(31, Math.max(1, parseInt(isoMatch[3], 10) || 1))
    return { dueDay: day, monthRef: `${y}-${m}` }
  }

  // Excel serial date
  const num = parseFloat(s)
  if (!isNaN(num) && num > 40000 && num < 60000) {
    const d = new Date(Math.round((num - 25569) * 86400 * 1000))
    if (!isNaN(d.getTime())) {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      return { dueDay: d.getDate(), monthRef: `${y}-${m}` }
    }
  }

  return { dueDay: 1, monthRef: defaultMonthRef }
}

function parseCategory(raw: unknown, categoriesList: CategoryTheme[] = CATEGORIES): string {
  if (!raw) return 'outros'
  const name = String(raw).trim().toLowerCase()
  const found = categoriesList.find((c) => c.name.toLowerCase() === name || c.id === name)
  return found ? found.id : 'outros'
}

function parseStatus(raw: unknown): 'pago' | 'pendente' {
  if (!raw) return 'pendente'
  const s = String(raw).trim().toLowerCase()
  return s === 'pago' || s === 'paid' ? 'pago' : 'pendente'
}

export function ImportModal({ T, theme, monthRef, categoriesList = CATEGORIES, onClose, onImport }: ImportModalProps) {
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
        month_ref: ['mes', 'mês', 'mes ref', 'mês ref', 'referencia', 'referência', 'month_ref', 'month ref', 'competencia', 'competência'],
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
      const { dueDay, monthRef: dateMonthRef } = parseDateField(mapping.due_date !== undefined ? row[mapping.due_date] : null, monthRef)
      
      let finalMonthRef = dateMonthRef
      if (mapping.month_ref !== undefined) {
        const explicitMonthRef = parseMonthRef(row[mapping.month_ref])
        if (explicitMonthRef) {
          finalMonthRef = explicitMonthRef
        }
      }

      const catKey = mapping['category'] ?? -1
      const category = catKey !== -1 ? parseCategory(row[catKey], categoriesList) : 'outros'
      const description = mapping.description !== undefined ? String(row[mapping.description] || '').trim() : '—'
      const amount = parseAmount(mapping.amount !== undefined ? row[mapping.amount] : 0)
      const paymentDay = mapping.payment_date !== undefined ? String(row[mapping.payment_date] || '').trim() : ''
      const status = parseStatus(mapping.status !== undefined ? row[mapping.status] : '')
      const observation = mapping.observation !== undefined ? String(row[mapping.observation] || '').trim() : ''

      const formattedDay = String(dueDay).padStart(2, '0')
      const dueDateIso = `${finalMonthRef}-${formattedDay}`

      return {
        id: `imp-${idC++}`,
        monthRef: finalMonthRef,
        dueDay,
        category,
        description,
        amount,
        paymentDay,
        status,
        observation,
        toNewExpense: (): NewExpense => ({
          due_date: dueDateIso,
          category_id: null,
          description,
          amount,
          payment_date: paymentDay || null,
          status,
          observation: observation || null,
          month_ref: finalMonthRef,
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
              {(() => {
                const monthCounts = preview.reduce((acc, row) => {
                  acc[row.monthRef] = (acc[row.monthRef] || 0) + 1
                  return acc
                }, {} as Record<string, number>)
                const monthRefsList = Object.keys(monthCounts).sort()

                return (
                  <>
                    <p className="text-sm mb-3" style={{ color: T.textMuted }}>
                      <strong>{preview.length}</strong> {preview.length === 1 ? 'registro pronto' : 'registros prontos'} para importar. Confira antes de confirmar:
                    </p>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {monthRefsList.map((mRef) => (
                        <span
                          key={mRef}
                          className="px-2.5 py-1 rounded-lg text-xs font-medium border"
                          style={{ backgroundColor: `${T.accent}15`, borderColor: `${T.accent}30`, color: T.accent }}
                        >
                          {monthLabel(mRef)}: <strong>{monthCounts[mRef]}</strong> {monthCounts[mRef] === 1 ? 'registro' : 'registros'}
                        </span>
                      ))}
                    </div>
                    <div className="overflow-x-auto rounded-xl border" style={{ borderColor: T.border }}>
                      <table className="w-full text-xs">
                        <thead>
                          <tr style={{ backgroundColor: `${T.border}60`, color: T.textFaint }}>
                            {['Dia', 'Mês Ref', 'Categoria', 'Descrição', 'Valor', 'Status'].map((h) => (
                              <th key={h} className="px-3 py-2 text-left font-medium">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {preview.slice(0, 10).map((row, i) => {
                            const cat = categoriesList.find((c) => c.id === row.category)
                            const catColor = theme === 'dark' ? cat?.dark : cat?.light
                            const isPago = row.status === 'pago'
                            return (
                              <tr key={i} style={{ borderTop: `1px solid ${T.borderSubtle}` }}>
                                <td className="px-3 py-2 font-mono" style={{ color: T.textMuted }}>
                                  {String(row.dueDay).padStart(2, '0')}
                                </td>
                                <td className="px-3 py-2 font-mono text-[11px]" style={{ color: T.textMuted }}>
                                  {monthLabel(row.monthRef)}
                                </td>
                                <td className="px-3 py-2">
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ backgroundColor: `${catColor || T.textFaint}20`, color: catColor || T.textFaint }}>
                                    {cat?.name || 'Outros'}
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
                  </>
                )
              })()}
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
