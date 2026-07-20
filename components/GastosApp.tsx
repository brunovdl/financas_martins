'use client'

import React, { useState, useMemo, useEffect, useCallback } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  Trash2,
  Link as LinkIcon,
  X,
  Wallet,
  CircleCheck,
  CircleDashed,
  Sun,
  Moon,
  Upload,
  Tag,
  Copy,
  Bell,
  Database,
} from 'lucide-react'
import { CATEGORIES, THEMES, formatBRL, monthLabel, shiftMonth, getCurrentMonthRef, getMaxDaysInMonth, type ThemeTokens, type CategoryTheme } from '@/lib/theme'
import { ProgressRing } from './ProgressRing'
import { ImportModal, type ParsedImportRow } from './ImportModal'
import { CategoriesModal } from './CategoriesModal'
import { CloneMonthModal } from './CloneMonthModal'
import { BackupModal } from './BackupModal'
import {
  fetchExpenses as fetchSupabaseExpenses,
  insertExpense as insertSupabaseExpense,
  updateExpense as updateSupabaseExpense,
  deleteExpense as deleteSupabaseExpense,
  bulkInsertExpenses as bulkInsertSupabaseExpenses,
  subscribeToExpenses,
  fetchCategories as fetchSupabaseCategories,
  insertCategory as insertSupabaseCategory,
  updateCategory as updateSupabaseCategory,
  deleteCategory as deleteSupabaseCategory,
  ensureBiweeklyBackup,
} from '@/lib/supabaseClient'
import type { Expense as SupabaseExpense, Category as SupabaseCategory } from '@/lib/types'

// Structure representing an expense in UI state
export interface UIExpense {
  id: string
  monthRef: string
  dueDay: number
  category: string
  description: string
  amount: number
  paymentDay: string
  status: 'pago' | 'pendente'
  observation: string
  // Original DB UUID if saved in Supabase
  dbId?: string
}

let idCounter = 1000
const nextId = () => `exp-${idCounter++}`

const MONTH_ABBRS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export function getTodayPaymentDay(): string {
  const d = new Date()
  const day = d.getDate()
  const monthAbbr = MONTH_ABBRS[d.getMonth()]
  return `${day}.${monthAbbr}`
}

export function getTodayIsoDate(): string {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatPaymentDateToUI(dateStr?: string | null): string {
  if (!dateStr) return ''
  if (dateStr.includes('-')) {
    const parts = dateStr.split('-')
    if (parts.length === 3) {
      const day = parseInt(parts[2], 10)
      const month = parseInt(parts[1], 10)
      if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
        return `${day}.${MONTH_ABBRS[month - 1]}`
      }
    }
  }
  return dateStr
}

const seedExpenses: UIExpense[] = [
  { id: nextId(), monthRef: '2026-04', dueDay: 5, category: 'outros', description: 'Empréstimo Rato (niver Miguel)', amount: 4350.00, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 6, category: 'daae', description: 'Água 03.2026 Araraquara', amount: 82.44, paymentDay: '2.abr', status: 'pago', observation: 'Matrícula: 1200534 Link: DAAE' },
  { id: nextId(), monthRef: '2026-04', dueDay: 6, category: 'outros', description: 'Primeira Semana Airbnb', amount: 600.00, paymentDay: '6.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 10, category: 'outros', description: 'Internet 04.2026', amount: 127.98, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 10, category: 'condinvest', description: 'Garagem 16 de 24', amount: 83.80, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 10, category: 'outros', description: 'Material Miguel 4 de 10', amount: 223.95, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 13, category: 'condinvest', description: 'Condomínio 04 de 12', amount: 342.10, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 15, category: 'outros', description: 'Empréstimo Rato (Receita e Escola)', amount: 3400.00, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 17, category: 'outros', description: 'Financiamento Carro 19 de 48', amount: 748.00, paymentDay: '6.abr', status: 'pago', observation: 'Pix: 10907124801' },
  { id: nextId(), monthRef: '2026-04', dueDay: 19, category: 'imposto', description: 'IPVA 04 de 05', amount: 253.73, paymentDay: '2.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 19, category: 'outros', description: 'Refinanciamento Pai (Creta) 7 de 13', amount: 1441.70, paymentDay: '6.abr', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 19, category: 'outros', description: 'Internet Celular Bia', amount: 50.00, paymentDay: '30.mar', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 19, category: 'outros', description: 'Condomínio (Condinveste Araraquara)', amount: 0.00, paymentDay: '', status: 'pendente', observation: 'Aguardando retorno fórum' },
  { id: nextId(), monthRef: '2026-04', dueDay: 20, category: 'caixa', description: 'Financiamento Apto Araraquara', amount: 605.05, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 20, category: 'outros', description: 'Cartão Mãe Bia Compras Niver Miguel 1 de 1', amount: 1500.00, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 20, category: 'outros', description: 'Cartão Mãe Bia Sofá 5 de 12', amount: 258.38, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 20, category: 'outros', description: 'Cartão Mãe Bia Material Miguel 3 de 5', amount: 260.27, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 20, category: 'outros', description: 'MEI Bia 03.2026', amount: 86.05, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 29, category: 'outros', description: 'Internet Celular Bruno', amount: 50.00, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 30, category: 'outros', description: 'Escola Miguel', amount: 850.00, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 30, category: 'cpfl', description: 'Energia', amount: 293.85, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-04', dueDay: 30, category: 'imposto', description: 'Negociação Receita Federal 06 de 60', amount: 2400.00, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-05', dueDay: 6, category: 'daae', description: 'Água 04.2026 Araraquara', amount: 79.10, paymentDay: '3.mai', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-05', dueDay: 10, category: 'condinvest', description: 'Garagem 17 de 24', amount: 83.80, paymentDay: '3.mai', status: 'pago', observation: '' },
  { id: nextId(), monthRef: '2026-05', dueDay: 13, category: 'condinvest', description: 'Condomínio 05 de 12', amount: 342.10, paymentDay: '', status: 'pendente', observation: '' },
  { id: nextId(), monthRef: '2026-05', dueDay: 30, category: 'cpfl', description: 'Energia', amount: 310.40, paymentDay: '', status: 'pendente', observation: '' },
]

function mapSupabaseToUI(e: SupabaseExpense, categoriesList: CategoryTheme[]): UIExpense {
  const dateObj = new Date(e.due_date + 'T00:00:00')
  const dueDay = isNaN(dateObj.getDate()) ? 1 : dateObj.getDate()
  const monthRef = e.month_ref ? e.month_ref.slice(0, 7) : getCurrentMonthRef()

  let catId = 'outros'
  if (e.category?.name) {
    const found = categoriesList.find((c) => c.name.toLowerCase() === e.category?.name.toLowerCase())
    if (found) catId = found.id
  } else if (e.category_id) {
    const foundDb = categoriesList.find((c) => c.dbId === e.category_id || c.id === e.category_id)
    if (foundDb) {
      catId = foundDb.id
    }
  }

  return {
    id: e.id,
    dbId: e.id,
    monthRef,
    dueDay,
    category: catId,
    description: e.description || '',
    amount: typeof e.amount === 'number' ? e.amount : parseFloat(String(e.amount)) || 0,
    paymentDay: formatPaymentDateToUI(e.payment_date),
    status: e.status,
    observation: e.observation || '',
  }
}

export default function GastosApp() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('mai_finance_theme') as 'dark' | 'light' | null
      if (savedTheme === 'dark' || savedTheme === 'light') return savedTheme
    }
    return 'dark'
  })
  const T: ThemeTokens = THEMES[theme]

  const [expenses, setExpenses] = useState<UIExpense[]>(seedExpenses)
  const [dbCategories, setDbCategories] = useState<SupabaseCategory[]>([])
  const [categoriesList, setCategoriesList] = useState<CategoryTheme[]>(CATEGORIES)
  const [showCategoriesModal, setShowCategoriesModal] = useState<boolean>(false)
  const [isSupabaseActive, setIsSupabaseActive] = useState<boolean>(false)
  const [monthRef, setMonthRef] = useState<string>(getCurrentMonthRef)
  const [search, setSearch] = useState('')
  const [onlyPending, setOnlyPending] = useState(false)
  const [editingCell, setEditingCell] = useState<{ id: string; field: keyof UIExpense } | null>(null)
  const [draft, setDraft] = useState('')
  const [showImport, setShowImport] = useState(false)
  const [showCloneModal, setShowCloneModal] = useState(false)
  const [showPrevMonthPanel, setShowPrevMonthPanel] = useState(false)
  const [showBackupModal, setShowBackupModal] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const handleToggleTheme = () => {
    setTheme((t) => {
      const next = t === 'dark' ? 'light' : 'dark'
      localStorage.setItem('mai_finance_theme', next)
      return next
    })
  }

  // Handlers para gerenciar categorias (adicionar, editar, deletar)
  const handleAddCategory = async (name: string, color: string) => {
    let dbId: string | undefined = undefined
    if (isSupabaseActive) {
      const created = await insertSupabaseCategory({ name, color })
      dbId = created?.id
    }
    const newCatId = name.toLowerCase().replace(/\s+/g, '-')
    const newCat: CategoryTheme = {
      id: newCatId,
      name,
      dark: color,
      light: color,
      dbId,
    }
    setCategoriesList((prev) => {
      const filtered = prev.filter((c) => c.id !== newCatId && c.name.toLowerCase() !== name.toLowerCase())
      return [newCat, ...filtered]
    })
    if (dbId) {
      setDbCategories((prev) => {
        const filtered = prev.filter((c) => c.id !== dbId && c.name.toLowerCase() !== name.toLowerCase())
        return [...filtered, { id: dbId!, name, color, created_at: new Date().toISOString() }]
      })
    }
  }

  const handleUpdateCategory = async (id: string, name: string, color: string) => {
    const target = categoriesList.find((c) => c.id === id)
    if (!target) return

    const dbCategory = dbCategories.find(
      (c) => c.id === target.dbId || c.name.toLowerCase() === target.name.toLowerCase()
    )
    const dbIdToUpdate = target.dbId || dbCategory?.id

    if (isSupabaseActive && dbIdToUpdate) {
      await updateSupabaseCategory(dbIdToUpdate, { name, color })
    }

    const updatedId = name.toLowerCase().replace(/\s+/g, '-')
    setCategoriesList((prev) =>
      prev.map((c) => (c.id === id ? { ...c, id: updatedId, name, dark: color, light: color } : c))
    )

    if (updatedId !== id) {
      setExpenses((prev) => prev.map((e) => (e.category === id ? { ...e, category: updatedId } : e)))
    }
  }

  const handleDeleteCategory = async (id: string) => {
    const target = categoriesList.find((c) => c.id === id)
    if (!target) return

    const dbCategory = dbCategories.find(
      (c) => c.id === target.dbId || c.name.toLowerCase() === target.name.toLowerCase()
    )
    const dbIdToDelete = target.dbId || dbCategory?.id

    if (isSupabaseActive && dbIdToDelete) {
      await deleteSupabaseCategory(dbIdToDelete)
      setDbCategories((prev) => prev.filter((c) => c.id !== dbIdToDelete))
    }

    setCategoriesList((prev) => prev.filter((c) => c.id !== id))
    setExpenses((prev) => prev.map((e) => (e.category === id ? { ...e, category: 'outros' } : e)))
  }

  // Tentar carregar dados do Supabase
  const loadSupabaseData = useCallback(async () => {
    try {
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
        return
      }
      let cats = await fetchSupabaseCategories().catch(() => [])

      // Se a tabela de categorias no Supabase estiver vazia, popular com as categorias iniciais
      if (cats.length === 0) {
        const seeded = await Promise.all(
          CATEGORIES.map((c) => insertSupabaseCategory({ name: c.name, color: c.dark }))
        ).catch(() => [])
        if (seeded.length > 0) {
          cats = seeded
        }
      }

      setDbCategories(cats)

      let currentCatsList = CATEGORIES
      if (cats && cats.length > 0) {
        const mapped = cats.map((c) => ({
          id: c.name.toLowerCase().trim().replace(/\s+/g, '-'),
          name: c.name,
          dark: c.color,
          light: c.color,
          dbId: c.id,
        }))
        const seenIds = new Set<string>()
        const uniqueCats: CategoryTheme[] = []
        for (const cat of mapped) {
          if (!seenIds.has(cat.id)) {
            seenIds.add(cat.id)
            uniqueCats.push(cat)
          }
        }
        currentCatsList = uniqueCats.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR', { sensitivity: 'base' }))
        setCategoriesList(currentCatsList)
      }

      const prevRef = shiftMonth(monthRef, -1)
      const [dbExps, prevDbExps] = await Promise.all([
        fetchSupabaseExpenses(monthRef),
        fetchSupabaseExpenses(prevRef).catch(() => []),
      ])

      if (dbExps) {
        setIsSupabaseActive(true)
        const mappedCurrent = dbExps.map((e) => mapSupabaseToUI(e, currentCatsList))
        const mappedPrev = (prevDbExps || []).map((e) => mapSupabaseToUI(e, currentCatsList))
        setExpenses((prev) => {
          const filtered = prev.filter((item) => item.monthRef !== monthRef && item.monthRef !== prevRef)
          return [...filtered, ...mappedCurrent, ...mappedPrev]
        })
      }
    } catch (e) {
      console.warn('Operando com dados locais (Supabase indisponível ou sem credenciais)', e)
      setIsSupabaseActive(false)
    }
  }, [monthRef])

  useEffect(() => {
    setShowPrevMonthPanel(false)
  }, [monthRef])

  useEffect(() => {
    let active = true
    Promise.resolve().then(() => {
      if (active) {
        loadSupabaseData()
      }
    })
    return () => {
      active = false
    }
  }, [loadSupabaseData])

  // Inscrever no Supabase Realtime se ativo
  useEffect(() => {
    if (!isSupabaseActive) return
    ensureBiweeklyBackup().catch(() => {})
    const unsubscribe = subscribeToExpenses(monthRef, () => {
      loadSupabaseData()
    })
    return () => {
      unsubscribe()
    }
  }, [isSupabaseActive, monthRef, loadSupabaseData])

  const monthExpenses = useMemo(() => {
    return expenses
      .filter((e) => e.monthRef === monthRef)
      .filter((e) => !onlyPending || e.status === 'pendente')
      .filter(
        (e) =>
          search.trim() === '' ||
          e.description.toLowerCase().includes(search.toLowerCase()) ||
          categoriesList.find((c) => c.id === e.category)?.name.toLowerCase().includes(search.toLowerCase())
      )
      .sort((a, b) => a.dueDay - b.dueDay)
  }, [expenses, monthRef, search, onlyPending, categoriesList])

  const [selectedIds, setSelectedIds] = useState<string[]>([])

  const toggleSelectAll = () => {
    if (monthExpenses.length === 0) return
    const allCurrentIds = monthExpenses.map((e) => e.id)
    const allSelected = allCurrentIds.every((id) => selectedIds.includes(id))
    if (allSelected) {
      setSelectedIds((prev) => prev.filter((id) => !allCurrentIds.includes(id)))
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...allCurrentIds])))
    }
  }

  const toggleSelectOne = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const removeSelectedExpenses = async () => {
    if (selectedIds.length === 0) return
    const idsToRemove = [...selectedIds]
    const itemsToRemove = expenses.filter((e) => idsToRemove.includes(e.id))

    setExpenses((prev) => prev.filter((e) => !idsToRemove.includes(e.id)))
    setSelectedIds([])

    if (isSupabaseActive) {
      try {
        await Promise.all(
          itemsToRemove
            .filter((e) => e.dbId)
            .map((e) => deleteSupabaseExpense(e.dbId!))
        )
      } catch (err) {
        console.error('Erro ao excluir registros selecionados no Supabase:', err)
      }
    }
  }

  const prevMonthRef = useMemo(() => shiftMonth(monthRef, -1), [monthRef])

  const prevMonthPendingExpenses = useMemo(() => {
    return expenses
      .filter((e) => e.monthRef === prevMonthRef && e.status === 'pendente')
      .sort((a, b) => a.dueDay - b.dueDay)
  }, [expenses, prevMonthRef])

  const prevMonthPendingTotal = useMemo(() => {
    return prevMonthPendingExpenses.reduce((s, e) => s + e.amount, 0)
  }, [prevMonthPendingExpenses])

  const totals = useMemo(() => {
    const all = expenses.filter((e) => e.monthRef === monthRef)
    const totalDespesas = all.reduce((s, e) => s + e.amount, 0)
    const totalPendente = all.filter((e) => e.status === 'pendente').reduce((s, e) => s + e.amount, 0)
    const totalPago = totalDespesas - totalPendente
    const pctPago = totalDespesas > 0 ? (totalPago / totalDespesas) * 100 : 0
    const qtdPendente = all.filter((e) => e.status === 'pendente').length
    return { totalDespesas, totalPendente, totalPago, pctPago, qtdPendente, qtdTotal: all.length }
  }, [expenses, monthRef])

  const selectedTotals = useMemo(() => {
    const selectedItems = expenses.filter((e) => selectedIds.includes(e.id))
    const total = selectedItems.reduce((s, e) => s + e.amount, 0)
    const totalPago = selectedItems.filter((e) => e.status === 'pago').reduce((s, e) => s + e.amount, 0)
    const totalPendente = selectedItems.filter((e) => e.status === 'pendente').reduce((s, e) => s + e.amount, 0)
    const countTotal = selectedItems.length
    const countPago = selectedItems.filter((e) => e.status === 'pago').length
    const countPendente = selectedItems.filter((e) => e.status === 'pendente').length
    return { total, totalPago, totalPendente, countTotal, countPago, countPendente }
  }, [expenses, selectedIds])

  const handleUpdateExpense = async (id: string, field: keyof UIExpense, value: unknown) => {
    setExpenses((prev) => prev.map((e) => (e.id === id ? { ...e, [field]: value } : e)))

    const item = expenses.find((e) => e.id === id)
    if (isSupabaseActive && item?.dbId) {
      try {
        const patch: Record<string, unknown> = {}
        if (field === 'dueDay') {
          const dayNum = Math.min(31, Math.max(1, Number(value) || 1))
          patch.due_date = `${monthRef}-${String(dayNum).padStart(2, '0')}`
        } else if (field === 'description') patch.description = value
        else if (field === 'amount') patch.amount = value
        else if (field === 'paymentDay') {
          let patchVal: string | null = null
          if (typeof value === 'string' && value.trim()) {
            const val = value.trim()
            if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
              patchVal = val
            } else {
              patchVal = getTodayIsoDate()
            }
          }
          patch.payment_date = patchVal
        }
        else if (field === 'status') patch.status = value
        else if (field === 'observation') patch.observation = value || null
        else if (field === 'category') {
          const catObj = categoriesList.find((c) => c.id === value)
          const dbCat = dbCategories.find((c) => c.name.toLowerCase() === catObj?.name.toLowerCase()) || (catObj?.dbId ? { id: catObj.dbId } : undefined)
          if (dbCat) patch.category_id = dbCat.id
        }

        await updateSupabaseExpense(item.dbId, patch)
      } catch (err) {
        console.error('Erro ao atualizar no Supabase:', err)
      }
    }
  }

  const toggleStatus = async (id: string) => {
    const item = expenses.find((e) => e.id === id)
    if (!item) return
    const nextStatus = item.status === 'pago' ? 'pendente' : 'pago'

    if (nextStatus === 'pago') {
      const todayPaymentDay = getTodayPaymentDay()
      const todayIsoDate = getTodayIsoDate()
      setExpenses((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'pago', paymentDay: todayPaymentDay } : e))
      )
      if (isSupabaseActive && item.dbId) {
        try {
          await updateSupabaseExpense(item.dbId, { status: 'pago', payment_date: todayIsoDate })
        } catch (err) {
          console.error('Erro ao atualizar no Supabase:', err)
        }
      }
    } else {
      handleUpdateExpense(id, 'status', nextStatus)
    }
  }

  const removeExpense = async (id: string) => {
    const item = expenses.find((e) => e.id === id)
    setExpenses((prev) => prev.filter((e) => e.id !== id))
    if (isSupabaseActive && item?.dbId) {
      try {
        await deleteSupabaseExpense(item.dbId)
      } catch (e) {
        console.error('Erro ao excluir no Supabase:', e)
      }
    }
  }

  const addExpense = async () => {
    const newLocalId = nextId()
    const newExp: UIExpense = {
      id: newLocalId,
      monthRef,
      dueDay: 1,
      category: 'outros',
      description: 'Nova despesa',
      amount: 0,
      paymentDay: '',
      status: 'pendente',
      observation: '',
    }
    setExpenses((prev) => [newExp, ...prev])
    setEditingCell({ id: newLocalId, field: 'description' })
    setDraft('Nova despesa')

    if (isSupabaseActive) {
      try {
        const catObj = dbCategories.find((c) => c.name.toLowerCase() === 'outros')
        const created = await insertSupabaseExpense({
          due_date: `${monthRef}-01`,
          category_id: catObj ? catObj.id : null,
          description: 'Nova despesa',
          amount: 0,
          payment_date: null,
          status: 'pendente',
          observation: null,
          month_ref: monthRef,
        })
        if (created?.id) {
          setExpenses((prev) =>
            prev.map((e) => (e.id === newLocalId ? { ...e, dbId: created.id, id: created.id } : e))
          )
          setEditingCell({ id: created.id, field: 'description' })
        }
      } catch (e) {
        console.error('Erro ao criar no Supabase:', e)
      }
    }
  }

  const startEdit = (id: string, field: keyof UIExpense, currentValue: unknown) => {
    setEditingCell({ id, field })
    setDraft(String(currentValue ?? ''))
  }

  const commitEdit = () => {
    if (!editingCell) return
    const { id, field } = editingCell
    let value: unknown = draft
    if (field === 'amount') value = parseFloat(draft.replace(',', '.')) || 0
    if (field === 'dueDay') value = Math.min(31, Math.max(1, parseInt(draft, 10) || 1))
    handleUpdateExpense(id, field, value)
    setEditingCell(null)
    setDraft('')
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setDraft('')
  }

  const handleImportRows = async (parsedRows: ParsedImportRow[]) => {
    if (parsedRows.length === 0) {
      setShowImport(false)
      return
    }

    const affectedMonths = Array.from(new Set(parsedRows.map((r) => r.monthRef))).sort()
    const monthNamesFormatted = affectedMonths.map((m) => monthLabel(m)).join(', ')

    if (isSupabaseActive) {
      try {
        const payload = parsedRows.map((r) => {
          const catObj = categoriesList.find((c) => c.id === r.category)
          const dbCat = dbCategories.find((c) => c.name.toLowerCase() === catObj?.name.toLowerCase()) || (catObj?.dbId ? { id: catObj.dbId } : undefined)
          const newExp = r.toNewExpense()
          newExp.category_id = dbCat ? dbCat.id : null
          return newExp
        })
        const createdList = await bulkInsertSupabaseExpenses(payload)
        const mapped = createdList.map((e) => mapSupabaseToUI(e, categoriesList))
        setExpenses((prev) => [...mapped, ...prev])
      } catch (e) {
        console.error('Erro na importação em lote do Supabase:', e)
      }
    } else {
      const localRows: UIExpense[] = parsedRows.map((r) => ({
        id: r.id || nextId(),
        monthRef: r.monthRef,
        dueDay: r.dueDay,
        category: r.category,
        description: r.description,
        amount: r.amount,
        paymentDay: r.paymentDay,
        status: r.status,
        observation: r.observation,
      }))
      setExpenses((prev) => [...localRows, ...prev])
    }
    setShowImport(false)

    const msg = `${parsedRows.length} ${parsedRows.length === 1 ? 'despesa importada' : 'despesas importadas'} com sucesso em ${affectedMonths.length} ${affectedMonths.length === 1 ? 'mês' : 'meses'} (${monthNamesFormatted}).`
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 6000)
  }

  const handleCloneMonth = async (fromMonth: string, toMonth: string) => {
    let sourceExpenses = expenses.filter((e) => e.monthRef === fromMonth)

    if (isSupabaseActive) {
      try {
        const dbSource = await fetchSupabaseExpenses(fromMonth)
        if (dbSource && dbSource.length > 0) {
          sourceExpenses = dbSource.map((e) => mapSupabaseToUI(e, categoriesList))
        }
      } catch (err) {
        console.error('Erro ao carregar despesas do mês de origem do Supabase:', err)
      }
    }

    if (sourceExpenses.length === 0) return

    const maxDaysInTargetMonth = getMaxDaysInMonth(toMonth)

    if (isSupabaseActive) {
      try {
        const payloadList = sourceExpenses.map((e) => {
          const catObj = categoriesList.find((c) => c.id === e.category)
          const dbCat = dbCategories.find((c) => c.name.toLowerCase() === catObj?.name.toLowerCase()) || (catObj?.dbId ? { id: catObj.dbId } : undefined)
          const validDueDay = Math.min(e.dueDay || 1, maxDaysInTargetMonth)

          return {
            month_ref: toMonth,
            due_date: `${toMonth}-${String(validDueDay).padStart(2, '0')}`,
            category_id: dbCat ? dbCat.id : (catObj?.dbId || null),
            description: e.description,
            amount: e.amount,
            payment_date: null,
            status: 'pendente' as const,
            observation: e.observation || null,
          }
        })

        const createdList = await bulkInsertSupabaseExpenses(payloadList)
        if (createdList && createdList.length > 0) {
          const mapped = createdList.map((item) => mapSupabaseToUI(item, categoriesList))
          setExpenses((prev) => [...mapped, ...prev])
        } else {
          const localCloned: UIExpense[] = sourceExpenses.map((e) => ({
            ...e,
            id: nextId(),
            dbId: undefined,
            monthRef: toMonth,
            dueDay: Math.min(e.dueDay || 1, maxDaysInTargetMonth),
            status: 'pendente',
            paymentDay: '',
          }))
          setExpenses((prev) => [...localCloned, ...prev])
        }
      } catch (err) {
        console.error('Erro ao clonar despesas no Supabase:', err)
        const localCloned: UIExpense[] = sourceExpenses.map((e) => ({
          ...e,
          id: nextId(),
          dbId: undefined,
          monthRef: toMonth,
          dueDay: Math.min(e.dueDay || 1, maxDaysInTargetMonth),
          status: 'pendente',
          paymentDay: '',
        }))
        setExpenses((prev) => [...localCloned, ...prev])
      }
    } else {
      const localCloned: UIExpense[] = sourceExpenses.map((e) => ({
        ...e,
        id: nextId(),
        dbId: undefined,
        monthRef: toMonth,
        dueDay: Math.min(e.dueDay || 1, maxDaysInTargetMonth),
        status: 'pendente',
        paymentDay: '',
      }))
      setExpenses((prev) => [...localCloned, ...prev])
    }

    setMonthRef(toMonth)
    const msg = `${sourceExpenses.length} ${sourceExpenses.length === 1 ? 'despesa clonada' : 'despesas clonadas'} com sucesso para ${monthLabel(toMonth)}.`
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 6000)
  }

  return (
    <div
      className="min-h-screen p-4 md:p-10 transition-all duration-300 relative"
      style={{
        background: T.pageBg,
        color: T.textPrimary,
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        paddingBottom: selectedIds.length > 0 ? '7.5rem' : undefined,
      }}
    >
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className="fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-lg border flex items-center gap-3 animate-in fade-in slide-in-from-top-3 duration-300 max-w-md"
          style={{ backgroundColor: T.surface, borderColor: `${T.accent}40`, color: T.textPrimary }}
        >
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: T.accent }} />
          <p className="text-xs font-medium leading-relaxed" style={{ color: T.textPrimary }}>
            {toastMessage}
          </p>
          <button
            onClick={() => setToastMessage(null)}
            className="p-1 text-xs rounded hover:opacity-80 ml-auto cursor-pointer"
            style={{ color: T.textFaint }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Painel Notificação Mês Anterior */}
      {showPrevMonthPanel && prevMonthPendingExpenses.length > 0 && (
        <div
          className="fixed top-5 left-1/2 -translate-x-1/2 z-50 w-[92%] max-w-xl rounded-2xl border shadow-2xl backdrop-blur-xl p-5 transition-all duration-300 animate-in fade-in slide-in-from-top-4"
          style={{
            backgroundColor: T.surface,
            borderColor: `${T.warning}55`,
            boxShadow: `0 20px 40px -12px rgba(0,0,0,0.5), 0 0 0 1px ${T.warning}22`,
          }}
        >
          <div className="flex items-center justify-between border-b pb-3 mb-3.5" style={{ borderColor: T.border }}>
            <div className="flex items-center gap-2.5">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold font-mono"
                style={{ backgroundColor: `${T.warning}20`, color: T.warning, border: `1px solid ${T.warning}40` }}
              >
                !
              </div>
              <div>
                <h3 className="text-sm font-semibold tracking-tight" style={{ color: T.textPrimary }}>
                  Despesas pendentes de {monthLabel(prevMonthRef)}
                </h3>
                <p className="text-[11px]" style={{ color: T.textFaint }}>
                  {prevMonthPendingExpenses.length} {prevMonthPendingExpenses.length === 1 ? 'pendência' : 'pendências'} • Total em aberto: <span className="font-mono font-medium" style={{ color: T.warning }}>{formatBRL(prevMonthPendingTotal)}</span>
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowPrevMonthPanel(false)}
              className="p-1.5 rounded-lg hover:opacity-80 transition-opacity cursor-pointer"
              style={{ color: T.textFaint }}
              aria-label="Fechar notificação"
            >
              <X size={16} />
            </button>
          </div>

          {/* Lista das despesas pendentes do mês anterior */}
          <div className="max-h-48 overflow-y-auto space-y-2 pr-1 mb-4">
            {prevMonthPendingExpenses.map((exp) => {
              const catObj = categoriesList.find((c) => c.id === exp.category)
              const catColor = catObj ? (theme === 'dark' ? catObj.dark : catObj.light) : T.textFaint
              return (
                <div
                  key={exp.id}
                  className="flex items-center justify-between p-2.5 rounded-xl border transition-colors text-xs"
                  style={{ backgroundColor: T.rowHover, borderColor: T.border }}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: catColor }}
                    />
                    <div className="truncate">
                      <p className="font-medium truncate" style={{ color: T.textPrimary }}>
                        {exp.description}
                      </p>
                      <p className="text-[10px]" style={{ color: T.textFaint }}>
                        Vencimento: Dia {exp.dueDay} • {catObj?.name || 'Outros'}
                      </p>
                    </div>
                  </div>
                  <span className="font-mono font-semibold flex-shrink-0 ml-3" style={{ color: T.warning }}>
                    {formatBRL(exp.amount)}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Botão de ação */}
          <div className="flex items-center justify-end pt-2 border-t" style={{ borderColor: T.border }}>
            <button
              onClick={() => {
                setMonthRef(prevMonthRef)
                setShowPrevMonthPanel(false)
              }}
              className="w-full sm:w-auto px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5 active:scale-95 shadow-md"
              style={{
                backgroundColor: T.warning,
                color: '#000000',
              }}
            >
              <span>Ver despesas de {monthLabel(prevMonthRef)}</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5 mb-8">
          <div className="flex items-center gap-3.5">
            <div
              className="w-11 h-11 rounded-2xl flex items-center justify-center"
              style={{
                background: `linear-gradient(135deg, ${T.accent}, ${T.accentTo})`,
                boxShadow: `0 0 24px -4px ${T.accent}80`,
              }}
            >
              <Wallet size={20} strokeWidth={2.2} style={{ color: T.accentOnBrand }} />
            </div>
            <div>
              <div className="text-[11px] tracking-[0.22em] font-mono font-medium mb-0.5" style={{ color: T.accent }}>
                CONTROLE FINANCEIRO {isSupabaseActive && <span className="ml-1 text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400">ONLINE</span>}
              </div>
              <h1 className="font-display text-2xl md:text-[28px] font-semibold tracking-tight leading-none">Gastos do mês</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            {/* Toggle de tema */}
            <button
              onClick={handleToggleTheme}
              className="p-2.5 rounded-full border transition-all active:scale-95 cursor-pointer"
              style={{ backgroundColor: `${T.surface}`, borderColor: T.border, color: T.textPrimary }}
              aria-label="Alternar tema"
              title={theme === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
            >
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {/* Ícone de notificação de pendências do mês anterior */}
            <button
              onClick={() => setShowPrevMonthPanel((v) => !v)}
              className="p-2.5 rounded-full border transition-all active:scale-95 flex items-center justify-center cursor-pointer relative"
              style={{
                backgroundColor: `${T.surface}`,
                borderColor: prevMonthPendingExpenses.length > 0 ? `${T.warning}88` : T.border,
                color: prevMonthPendingExpenses.length > 0 ? T.warning : T.textMuted,
              }}
              aria-label="Despesas pendentes do mês anterior"
              title={
                prevMonthPendingExpenses.length > 0
                  ? `${prevMonthPendingExpenses.length} ${prevMonthPendingExpenses.length === 1 ? 'despesa pendente' : 'despesas pendentes'} em ${monthLabel(prevMonthRef)}`
                  : `Nenhuma pendência em ${monthLabel(prevMonthRef)}`
              }
            >
              <Bell size={16} />
              {prevMonthPendingExpenses.length > 0 && (
                <span
                  className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold font-mono flex items-center justify-center border shadow-sm"
                  style={{
                    backgroundColor: T.warning,
                    color: '#000000',
                    borderColor: T.surface,
                  }}
                >
                  {prevMonthPendingExpenses.length}
                </span>
              )}
            </button>

            {/* Ícone de Backups & Restauração */}
            <button
              onClick={() => setShowBackupModal(true)}
              className="p-2.5 rounded-full border transition-all active:scale-95 flex items-center justify-center cursor-pointer"
              style={{ backgroundColor: `${T.surface}`, borderColor: T.border, color: T.textPrimary }}
              aria-label="Backups e Restauração"
              title="Gerenciar backups e restauração de dados"
            >
              <Database size={16} />
            </button>

            {/* Seletor de mês com botão de clonar */}
            <div className="flex items-center gap-1.5">
              <div
                className="flex items-center gap-1 backdrop-blur border rounded-full px-1.5 py-1.5"
                style={{ backgroundColor: T.surface, borderColor: T.border }}
              >
                <button
                  onClick={() => setMonthRef((m) => shiftMonth(m, -1))}
                  className="p-2 rounded-full active:scale-95 transition-all cursor-pointer"
                  style={{ color: T.textPrimary }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = T.rowHover)}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  aria-label="Mês anterior"
                >
                  <ChevronLeft size={16} />
                </button>
                <div className="w-40 text-center font-display text-sm font-medium">{monthLabel(monthRef)}</div>
                <button
                  onClick={() => setMonthRef((m) => shiftMonth(m, 1))}
                  className="p-2 rounded-full active:scale-95 transition-all cursor-pointer"
                  style={{ color: T.textPrimary }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = T.rowHover)}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  aria-label="Próximo mês"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
              <button
                onClick={() => setShowCloneModal(true)}
                className="p-2.5 rounded-full border transition-all active:scale-95 flex items-center justify-center cursor-pointer"
                style={{ backgroundColor: `${T.surface}`, borderColor: T.border, color: T.textPrimary }}
                aria-label="Clonar despesas deste mês"
                title="Clonar despesas de um mês para outro"
              >
                <Copy size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div
            className="col-span-2 md:col-span-1 rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.border, background: `linear-gradient(135deg, ${T.surfaceGradientA}, ${T.surfaceGradientB})` }}
          >
            <span className="text-[11px] font-medium tracking-wide" style={{ color: T.textFaint }}>
              TOTAL DO MÊS
            </span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalDespesas)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>
              {totals.qtdTotal} lançamentos
            </span>
          </div>

          <div
            className="rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.successBorder, background: T.successBg }}
          >
            <span className="text-[11px] font-medium tracking-wide flex items-center gap-1" style={{ color: T.successText }}>
              <CircleCheck size={12} /> PAGO
            </span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalPago)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>
              {totals.qtdTotal - totals.qtdPendente} itens quitados
            </span>
          </div>

          <div
            className="rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.warningBorder, background: T.warningBg }}
          >
            <span className="text-[11px] font-medium tracking-wide flex items-center gap-1" style={{ color: T.warning }}>
              <CircleDashed size={12} /> PENDENTE
            </span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalPendente)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>
              {totals.qtdPendente} em aberto
            </span>
          </div>

          <div
            className="rounded-2xl border p-4 flex items-center gap-3"
            style={{ borderColor: T.border, background: `linear-gradient(135deg, ${T.surfaceGradientA}, ${T.surfaceGradientB})` }}
          >
            <ProgressRing pct={totals.pctPago} size={52} T={T} />
            <div>
              <div className="font-mono text-lg font-semibold leading-none">{totals.pctPago.toFixed(0)}%</div>
              <div className="text-[11px] mt-1" style={{ color: T.textFaint }}>
                do mês quitado
              </div>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-2.5 mb-4">
          <div
            className="flex items-center gap-2 border rounded-xl px-3.5 py-2.5 flex-1 transition-colors"
            style={{ backgroundColor: T.surface, borderColor: T.border }}
          >
            <Search size={15} style={{ color: T.textFaint }} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por descrição ou categoria..."
              className="bg-transparent outline-none text-sm flex-1"
              style={{ color: T.textPrimary }}
            />
          </div>
          <button
            onClick={() => setOnlyPending((v) => !v)}
            className="px-4 py-2.5 rounded-xl text-sm font-medium border transition-all"
            style={
              onlyPending
                ? { backgroundColor: `${T.warning}1A`, borderColor: `${T.warning}66`, color: T.warning }
                : { backgroundColor: T.surface, borderColor: T.border, color: T.textMuted }
            }
          >
            Só pendentes
          </button>
          {selectedIds.length > 0 && (
            <button
              onClick={removeSelectedExpenses}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98]"
              style={{ backgroundColor: `${T.danger}20`, borderColor: `${T.danger}66`, color: T.danger, borderStyle: 'solid', borderWidth: '1px' }}
            >
              <Trash2 size={15} strokeWidth={2} /> Excluir ({selectedIds.length})
            </button>
          )}
          <button
            onClick={() => setShowCategoriesModal(true)}
            className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all hover:opacity-90 active:scale-[0.98]"
            style={{ backgroundColor: T.surface, borderColor: T.border, color: T.textMuted }}
          >
            <Tag size={15} strokeWidth={2} /> Categorias
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all hover:opacity-90 active:scale-[0.98]"
            style={{ backgroundColor: T.surface, borderColor: T.border, color: T.textMuted }}
          >
            <Upload size={15} strokeWidth={2} /> Importar
          </button>
          <button
            onClick={addExpense}
            className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold hover:opacity-90 active:scale-[0.98] transition-all"
            style={{ background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`, color: T.accentOnBrand }}
          >
            <Plus size={16} strokeWidth={2.5} /> Nova despesa
          </button>
        </div>

        {/* Table */}
        <div className="backdrop-blur border rounded-2xl overflow-hidden" style={{ backgroundColor: T.surface, borderColor: T.border }}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wider" style={{ color: T.textFaint }}>
                  <th className="px-3 py-3 w-10 text-center" style={{ borderBottom: `1px solid ${T.border}` }}>
                    <input
                      type="checkbox"
                      checked={monthExpenses.length > 0 && monthExpenses.every((e) => selectedIds.includes(e.id))}
                      onChange={toggleSelectAll}
                      className="rounded cursor-pointer accent-emerald-500 w-4 h-4 align-middle"
                      title={selectedIds.length > 0 ? "Desmarcar todos" : "Selecionar todos"}
                    />
                  </th>
                  <th className="px-4 py-3 font-medium w-24" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Vencimento
                  </th>
                  <th className="px-4 py-3 font-medium w-32" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Categoria
                  </th>
                  <th className="px-4 py-3 font-medium" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Descrição
                  </th>
                  <th className="px-4 py-3 font-medium text-right w-28" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Valor
                  </th>
                  <th className="px-4 py-3 font-medium w-24" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Pagamento
                  </th>
                  <th className="px-4 py-3 font-medium w-28" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Status
                  </th>
                  <th className="px-4 py-3 font-medium" style={{ borderBottom: `1px solid ${T.border}` }}>
                    Observação
                  </th>
                  <th className="px-2 py-3 w-8" style={{ borderBottom: `1px solid ${T.border}` }}></th>
                </tr>
              </thead>
              <tbody>
                {monthExpenses.map((e) => {
                  const cat = categoriesList.find((c) => c.id === e.category)
                  const catColor = theme === 'dark' ? cat?.dark : cat?.light
                  const isPago = e.status === 'pago'
                  const stripeColor = isPago ? T.success : T.warning
                  const monthAbbr = monthLabel(monthRef).slice(0, 3).toLowerCase()
                  const isSelected = selectedIds.includes(e.id)

                  return (
                    <tr
                      key={e.id}
                      className="group transition-colors"
                      style={{ backgroundColor: isSelected ? `${T.accent}12` : 'transparent' }}
                      onMouseEnter={(ev) => (ev.currentTarget.style.backgroundColor = isSelected ? `${T.accent}20` : T.rowHover)}
                      onMouseLeave={(ev) => (ev.currentTarget.style.backgroundColor = isSelected ? `${T.accent}12` : 'transparent')}
                    >
                      {/* Checkbox de Seleção */}
                      <td className="px-3 py-2.5 text-center relative" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectOne(e.id)}
                          className="rounded cursor-pointer accent-emerald-500 w-4 h-4 align-middle"
                        />
                      </td>
                      {/* Vencimento — com stripe de status */}
                      <td className="px-4 py-2.5 font-mono text-[13px] relative" style={{ color: T.textMuted, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <span className="absolute left-0 top-1.5 bottom-1.5 w-[2.5px] rounded-full" style={{ backgroundColor: stripeColor, opacity: 0.8 }} />
                        <span className="pl-2">
                          {editingCell?.id === e.id && editingCell.field === 'dueDay' ? (
                            <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} T={T} />
                          ) : (
                            <button onClick={() => startEdit(e.id, 'dueDay', e.dueDay)} className="hover:opacity-70 transition-opacity" style={{ color: 'inherit' }}>
                              {String(e.dueDay).padStart(2, '0')}.{monthAbbr}
                            </button>
                          )}
                        </span>
                      </td>

                      {/* Categoria */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <select
                          value={e.category}
                          onChange={(ev) => handleUpdateExpense(e.id, 'category', ev.target.value)}
                          className="text-[11px] font-semibold rounded-full px-2.5 py-1 border-0 outline-none cursor-pointer appearance-none"
                          style={{ backgroundColor: `${catColor || T.textFaint}20`, color: catColor || T.textFaint }}
                        >
                          {categoriesList.map((c, idx) => (
                            <option key={c.dbId ? `${c.id}-${c.dbId}` : `${c.id}-${idx}`} value={c.id} style={{ backgroundColor: T.surfaceSolid, color: T.textPrimary }}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                      </td>

                      {/* Descrição */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === 'description' ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} wide T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, 'description', e.description)}
                            className="text-left transition-colors"
                            style={{ color: T.textPrimary }}
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.accent)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                          >
                            {e.description}
                          </button>
                        )}
                      </td>

                      {/* Valor */}
                      <td className="px-4 py-2.5 text-right font-mono" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === 'amount' ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} align="right" T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, 'amount', e.amount)}
                            className="font-medium transition-colors"
                            style={{ color: T.textPrimary }}
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.accent)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                          >
                            {formatBRL(e.amount)}
                          </button>
                        )}
                      </td>

                      {/* Pagamento */}
                      <td className="px-4 py-2.5 font-mono text-xs" style={{ color: T.textFaint, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === 'paymentDay' ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} T={T} />
                        ) : (
                          <button onClick={() => startEdit(e.id, 'paymentDay', e.paymentDay)} className="hover:opacity-70 transition-opacity">
                            {e.paymentDay || '—'}
                          </button>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <button
                          onClick={() => toggleStatus(e.id)}
                          className="text-[11px] font-semibold px-2.5 py-1 rounded-full transition-colors flex items-center gap-1 w-fit"
                          style={
                            isPago
                              ? { backgroundColor: `${T.success}1F`, color: T.successText }
                              : { backgroundColor: `${T.warning}1F`, color: T.warning }
                          }
                        >
                          {isPago ? <CircleCheck size={11} /> : <CircleDashed size={11} />}
                          {isPago ? 'Pago' : 'Pendente'}
                        </button>
                      </td>

                      {/* Observação */}
                      <td className="px-4 py-2.5 text-xs" style={{ color: T.textMuted, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === 'observation' ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} wide T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, 'observation', e.observation)}
                            className="text-left transition-colors flex items-center gap-1"
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textMuted)}
                          >
                            {e.observation && <LinkIcon size={11} className="shrink-0" />}
                            {e.observation || '—'}
                          </button>
                        )}
                      </td>

                      {/* Delete */}
                      <td className="px-2 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <button
                          onClick={() => removeExpense(e.id)}
                          className="p-1 rounded opacity-0 group-hover:opacity-100 transition-all"
                          style={{ color: T.textFaint }}
                          onMouseEnter={(ev) => {
                            ev.currentTarget.style.color = T.danger
                            ev.currentTarget.style.backgroundColor = `${T.danger}1A`
                          }}
                          onMouseLeave={(ev) => {
                            ev.currentTarget.style.color = T.textFaint
                            ev.currentTarget.style.backgroundColor = 'transparent'
                          }}
                          aria-label="Remover"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
                {monthExpenses.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-sm" style={{ color: T.textFaint }}>
                      Nenhuma despesa encontrada para {monthLabel(monthRef)}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="text-xs mt-4 text-center" style={{ color: T.textFaint }}>
          {isSupabaseActive
            ? 'Conectado ao Supabase com sincronização em tempo real · clique em qualquer célula para editar'
            : 'Modo demonstração (dados em memória) · clique em qualquer célula para editar'}
        </p>
      </div>

      {/* Floating Selection Bar */}
      {selectedIds.length > 0 && (
        <div
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 px-5 py-3.5 rounded-2xl border flex flex-wrap items-center justify-between gap-4 sm:gap-6 backdrop-blur-md animate-in fade-in slide-in-from-bottom-5 duration-300 max-w-[92vw] sm:max-w-2xl w-full"
          style={{
            backgroundColor: `${T.surface}EE`,
            borderColor: `${T.accent}60`,
            boxShadow: `0 16px 40px -8px rgba(0,0,0,0.35), 0 0 20px 0 ${T.accent}20`,
          }}
        >
          {/* Lado esquerdo: Seleção e Soma Total */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-[11px] uppercase tracking-wider font-semibold font-mono" style={{ color: T.accent }}>
                {selectedTotals.countTotal} {selectedTotals.countTotal === 1 ? 'item selecionado' : 'itens selecionados'}
              </span>
              <span className="font-mono text-lg font-bold" style={{ color: T.textPrimary }}>
                {formatBRL(selectedTotals.total)}
              </span>
            </div>

            {/* Divisora vertical */}
            <div className="h-8 w-px hidden sm:block" style={{ backgroundColor: T.border }} />

            {/* Sub-totais: Pago e Pendente */}
            <div className="hidden sm:flex items-center gap-3 text-xs">
              {selectedTotals.countPago > 0 && (
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-mono" style={{ borderColor: T.successBorder, backgroundColor: T.successBg, color: T.successText }}>
                  <CircleCheck size={13} />
                  <span>Pago: <strong>{formatBRL(selectedTotals.totalPago)}</strong> ({selectedTotals.countPago})</span>
                </div>
              )}
              {selectedTotals.countPendente > 0 && (
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-mono" style={{ borderColor: T.warningBorder, backgroundColor: T.warningBg, color: T.warning }}>
                  <CircleDashed size={13} />
                  <span>Pendente: <strong>{formatBRL(selectedTotals.totalPendente)}</strong> ({selectedTotals.countPendente})</span>
                </div>
              )}
            </div>
          </div>

          {/* Lado direito: Ações */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1.5 rounded-xl text-xs font-medium border transition-all hover:opacity-80 active:scale-95 cursor-pointer"
              style={{ backgroundColor: 'transparent', borderColor: T.border, color: T.textMuted }}
            >
              Desmarcar todos
            </button>
            <button
              onClick={removeSelectedExpenses}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all hover:opacity-90 active:scale-95 cursor-pointer"
              style={{ backgroundColor: `${T.danger}20`, borderColor: `${T.danger}66`, color: T.danger }}
            >
              <Trash2 size={13} strokeWidth={2} /> Excluir ({selectedIds.length})
            </button>
          </div>
        </div>
      )}

      {/* Categories Modal */}
      {showCategoriesModal && (
        <CategoriesModal
          T={T}
          categories={categoriesList}
          onClose={() => {
            setCategoriesList((prev) =>
              [...prev].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR', { sensitivity: 'base' }))
            )
            setShowCategoriesModal(false)
          }}
          onAddCategory={handleAddCategory}
          onUpdateCategory={handleUpdateCategory}
          onDeleteCategory={handleDeleteCategory}
        />
      )}

      {/* Import Modal */}
      {showImport && (
        <ImportModal
          T={T}
          theme={theme}
          monthRef={monthRef}
          categoriesList={categoriesList}
          onClose={() => setShowImport(false)}
          onImport={handleImportRows}
        />
      )}

      {/* Clone Month Modal */}
      {showCloneModal && (
        <CloneMonthModal
          T={T}
          currentMonthRef={monthRef}
          allExpenses={expenses}
          onClose={() => setShowCloneModal(false)}
          onClone={handleCloneMonth}
        />
      )}

      {showBackupModal && (
        <BackupModal
          T={T}
          onClose={() => setShowBackupModal(false)}
          onRestored={async () => {
            await loadSupabaseData()
            const msg = 'Dados do banco de dados restaurados com sucesso!'
            setToastMessage(msg)
            setTimeout(() => setToastMessage(null), 6000)
          }}
        />
      )}
    </div>
  )
}

function EditInput({
  draft,
  setDraft,
  onCommit,
  onCancel,
  align,
  wide,
  T,
}: {
  draft: string
  setDraft: (val: string) => void
  onCommit: () => void
  onCancel: () => void
  align?: 'right'
  wide?: boolean
  T: ThemeTokens
}) {
  return (
    <div className="flex items-center gap-1">
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onCommit()
          if (e.key === 'Escape') onCancel()
        }}
        onBlur={onCommit}
        className={`border rounded-lg px-2 py-1 outline-none ${wide ? 'w-full min-w-[160px]' : 'w-20'} ${align === 'right' ? 'text-right' : ''}`}
        style={{ backgroundColor: T.inputBg, borderColor: T.accent, color: T.textPrimary }}
      />
      <button
        onMouseDown={(e) => {
          e.preventDefault()
          onCancel()
        }}
        style={{ color: T.textFaint }}
      >
        <X size={12} />
      </button>
    </div>
  )
}
