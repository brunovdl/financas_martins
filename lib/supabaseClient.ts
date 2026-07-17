import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import type { Category, Expense, MonthlySummary, NewExpense, NewCategory, PatchExpense } from './types'

// ---------------------------------------------------------------------------
// Singleton client
// ---------------------------------------------------------------------------
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder'

export const supabase = createSupabaseClient(supabaseUrl, supabaseAnonKey)

// ---------------------------------------------------------------------------
// Helpers de conversão — banco usa ISO date string, frontend usa dueDay (number)
// monthRef no banco: "2026-04-01" | no frontend: "2026-04"
// ---------------------------------------------------------------------------
export function monthRefToDate(monthRef: string): string {
  return `${monthRef}-01`
}

export function dateToMonthRef(isoDate: string): string {
  return isoDate.slice(0, 7) // "2026-04-01" → "2026-04"
}

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------
export async function fetchCategories(): Promise<Category[]> {
  const { data, error } = await supabase
    .from('categories')
    .select('*')
    .order('name')
  if (error) throw error
  return data ?? []
}

export async function insertCategory(cat: NewCategory): Promise<Category> {
  const { data, error } = await supabase
    .from('categories')
    .insert(cat)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function deleteCategory(id: string): Promise<void> {
  const { error } = await supabase
    .from('categories')
    .delete()
    .eq('id', id)
  if (error) throw error
}

// ---------------------------------------------------------------------------
// Expenses
// ---------------------------------------------------------------------------
export async function fetchExpenses(monthRef: string): Promise<Expense[]> {
  const monthDate = monthRefToDate(monthRef) // "2026-04-01"
  const { data, error } = await supabase
    .from('expenses')
    .select('*, category:categories(*)')
    .eq('month_ref', monthDate)
    .order('due_date', { ascending: true })
  if (error) throw error
  return (data ?? []) as Expense[]
}

export async function insertExpense(expense: NewExpense): Promise<Expense> {
  const payload = {
    ...expense,
    month_ref: monthRefToDate(expense.month_ref),
  }
  const { data, error } = await supabase
    .from('expenses')
    .insert(payload)
    .select('*, category:categories(*)')
    .single()
  if (error) throw error
  return data as Expense
}

export async function updateExpense(id: string, patch: PatchExpense): Promise<Expense> {
  const payload: Record<string, unknown> = { ...patch }
  if (payload.month_ref) {
    payload.month_ref = monthRefToDate(payload.month_ref as string)
  }
  const { data, error } = await supabase
    .from('expenses')
    .update(payload)
    .eq('id', id)
    .select('*, category:categories(*)')
    .single()
  if (error) throw error
  return data as Expense
}

export async function deleteExpense(id: string): Promise<void> {
  const { error } = await supabase
    .from('expenses')
    .delete()
    .eq('id', id)
  if (error) throw error
}

export async function bulkInsertExpenses(expenses: NewExpense[]): Promise<Expense[]> {
  const payload = expenses.map((e) => ({
    ...e,
    month_ref: monthRefToDate(e.month_ref),
  }))
  const { data, error } = await supabase
    .from('expenses')
    .insert(payload)
    .select('*, category:categories(*)')
  if (error) throw error
  return (data ?? []) as Expense[]
}

// ---------------------------------------------------------------------------
// Monthly summary (view)
// ---------------------------------------------------------------------------
export async function fetchMonthlySummary(monthRef: string): Promise<MonthlySummary | null> {
  const monthDate = monthRefToDate(monthRef)
  const { data, error } = await supabase
    .from('monthly_summary')
    .select('*')
    .eq('month_ref', monthDate)
    .single()
  if (error && error.code !== 'PGRST116') throw error // PGRST116 = not found
  return data ?? null
}

// ---------------------------------------------------------------------------
// Realtime
// ---------------------------------------------------------------------------
type RealtimeCallback = (payload: { eventType: string; new: Expense; old: Expense }) => void

export function subscribeToExpenses(monthRef: string, callback: RealtimeCallback) {
  const monthDate = monthRefToDate(monthRef)
  const channel = supabase
    .channel(`expenses:${monthRef}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'expenses',
        filter: `month_ref=eq.${monthDate}`,
      },
      (payload) => callback(payload as unknown as Parameters<RealtimeCallback>[0])
    )
    .subscribe()
  return () => {
    supabase.removeChannel(channel)
  }
}
