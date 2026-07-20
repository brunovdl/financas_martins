import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import type { Category, Expense, MonthlySummary, NewExpense, NewCategory, PatchExpense, BackupRecord } from './types'

// ---------------------------------------------------------------------------
// Singleton client
// ---------------------------------------------------------------------------
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder'

const globalForSupabase = globalThis as unknown as {
  supabaseClient?: ReturnType<typeof createSupabaseClient>
}

export const supabase =
  globalForSupabase.supabaseClient ??
  createSupabaseClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
  })

if (process.env.NODE_ENV !== 'production') {
  globalForSupabase.supabaseClient = supabase
}

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

// Helper para lidar com tabelas do Supabase sem schema estático gerado
/* eslint-disable-next-line @typescript-eslint/no-explicit-any */
const fromTable = (tableName: string) => (supabase as any).from(tableName)

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------
export async function fetchCategories(): Promise<Category[]> {
  const { data, error } = await fromTable('categories')
    .select('*')
    .order('name')
  if (error) throw error
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
  return (data ?? []).map((c: any) => ({
    ...c,
    color: c.color_hex || c.color || '#94A3B8',
  }))
}

export async function insertCategory(cat: NewCategory): Promise<Category> {
  const payload: Record<string, unknown> = {
    name: cat.name,
    color_hex: cat.color,
    type: 'DESPESA',
    icon: 'tag',
  }

  const { data, error } = await fromTable('categories')
    .insert(payload)
    .select()
    .single()

  if (error) {
    if (error.code === '23505' || error.message?.includes('duplicate')) {
      const { data: existing, error: fetchErr } = await fromTable('categories')
        .update({ color_hex: cat.color })
        .eq('name', cat.name)
        .select()
        .single()
      if (fetchErr) throw fetchErr
      return { ...existing, color: existing.color_hex || existing.color || cat.color }
    }
    throw error
  }
  return { ...data, color: data.color_hex || data.color || cat.color }
}

export async function updateCategory(id: string, patch: Partial<NewCategory>): Promise<Category> {
  const payload: Record<string, unknown> = {}
  if (patch.name) payload.name = patch.name
  if (patch.color) payload.color_hex = patch.color

  const { data, error } = await fromTable('categories')
    .update(payload)
    .eq('id', id)
    .select()
    .single()
  if (error) throw error
  return { ...data, color: data.color_hex || data.color || patch.color }
}

export async function unlinkExpensesFromCategory(categoryId: string): Promise<void> {
  const { error } = await fromTable('expenses')
    .update({ category_id: null })
    .eq('category_id', categoryId)
  if (error) console.warn('Erro ao desvincular despesas da categoria:', error)
}

export async function deleteCategory(id: string): Promise<void> {
  await unlinkExpensesFromCategory(id)
  const { error } = await fromTable('categories')
    .delete()
    .eq('id', id)
  if (error) throw error
}

// ---------------------------------------------------------------------------
// Expenses
// ---------------------------------------------------------------------------
export async function fetchExpenses(monthRef: string): Promise<Expense[]> {
  const monthDate = monthRefToDate(monthRef) // "2026-04-01"
  const { data, error } = await fromTable('expenses')
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
  const { data, error } = await fromTable('expenses')
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
  const { data, error } = await fromTable('expenses')
    .update(payload)
    .eq('id', id)
    .select('*, category:categories(*)')
    .single()
  if (error) throw error
  return data as Expense
}

export async function deleteExpense(id: string): Promise<void> {
  const { error } = await fromTable('expenses')
    .delete()
    .eq('id', id)
  if (error) throw error
}

export async function bulkInsertExpenses(expenses: NewExpense[]): Promise<Expense[]> {
  const payload = expenses.map((e) => ({
    ...e,
    month_ref: monthRefToDate(e.month_ref),
  }))
  const { data, error } = await fromTable('expenses')
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

// ---------------------------------------------------------------------------
// Backups & Restore
// ---------------------------------------------------------------------------
export async function fetchBackups(): Promise<BackupRecord[]> {
  try {
    const { data, error } = await fromTable('backups')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) {
      console.warn('Aviso ao consultar backups:', error.message || error)
      return []
    }
    return (data ?? []) as BackupRecord[]
  } catch (err) {
    console.warn('Erro ao buscar backups do Supabase:', err)
    return []
  }
}

export async function pruneOldBackups(keepLimit = 3): Promise<void> {
  try {
    const { data: backups } = await fromTable('backups')
      .select('id, created_at')
      .order('created_at', { ascending: false })

    if (backups && backups.length > keepLimit) {
      const idsToDelete = backups.slice(keepLimit).map((b: { id: string }) => b.id)
      await fromTable('backups').delete().in('id', idsToDelete)
    }
  } catch (err) {
    console.warn('Aviso ao aplicar política de retenção de backups:', err)
  }
}

export async function createBackup(type: 'automatico' | 'manual' = 'manual'): Promise<BackupRecord> {
  // Tentar via RPC `create_backup` primeiro
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
  const { data: rpcData, error: rpcError } = await (supabase as any).rpc('create_backup', { backup_type: type })
  if (!rpcError && rpcData) {
    const { data: fetched, error: fetchErr } = await fromTable('backups')
      .select('*')
      .eq('id', rpcData)
      .single()
    if (!fetchErr && fetched) return fetched as BackupRecord
  }

  // Fallback em JS client-side caso a RPC/função PostgreSQL ainda não esteja cadastrada no Supabase
  const [allCats, allExps] = await Promise.all([
    fetchCategories().catch(() => []),
    fromTable('expenses').select('*').catch(() => ({ data: [] })),
  ])

  const categories = allCats || []
  const expenses = (allExps.data || []) as Expense[]
  const totalAmount = expenses.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)

  const payload = {
    type,
    categories_count: categories.length,
    expenses_count: expenses.length,
    total_amount: totalAmount,
    data: {
      categories,
      expenses,
    },
  }

  const { data, error } = await fromTable('backups')
    .insert(payload)
    .select()
    .single()

  if (error) throw error

  // Executar limpeza de retenção no fallback
  await pruneOldBackups(3)

  return data as BackupRecord
}

export async function restoreBackup(backupId: string): Promise<{ categories_restored: number; expenses_restored: number }> {
  // Buscar o snapshot do backup
  const { data: backup, error: fetchErr } = await fromTable('backups')
    .select('*')
    .eq('id', backupId)
    .single()
  if (fetchErr || !backup) throw fetchErr || new Error('Backup não encontrado')

  const snapshot = backup as BackupRecord
  const { categories, expenses } = snapshot.data

  // 1. Limpar todas as despesas e categorias existentes
  await fromTable('expenses').delete().neq('id', '00000000-0000-0000-0000-000000000000')
  await fromTable('categories').delete().neq('id', '00000000-0000-0000-0000-000000000000')

  // 2. Restaurar categorias mantendo os IDs originais se possível
  if (categories && categories.length > 0) {
    const catsPayload = categories.map((c) => ({
      id: c.id,
      name: c.name,
      color_hex: c.color || c.color_hex || '#94A3B8',
    }))
    const { error: catErr } = await fromTable('categories').insert(catsPayload)
    if (catErr) console.warn('Aviso ao restaurar categorias:', catErr)
  }

  // 3. Restaurar despesas mantendo os IDs originais se possível
  if (expenses && expenses.length > 0) {
    const expsPayload = expenses.map((e) => ({
      id: e.id,
      due_date: e.due_date,
      category_id: e.category_id,
      description: e.description,
      amount: e.amount,
      payment_date: e.payment_date,
      status: e.status,
      observation: e.observation,
      month_ref: e.month_ref,
    }))
    const { error: expErr } = await fromTable('expenses').insert(expsPayload)
    if (expErr) console.warn('Aviso ao restaurar despesas:', expErr)
  }

  return {
    categories_restored: categories ? categories.length : 0,
    expenses_restored: expenses ? expenses.length : 0,
  }
}

export async function ensureBiweeklyBackup(): Promise<boolean> {
  try {
    const today = new Date()
    const day = today.getDate()
    // Executa no dia 1 e dia 15
    if (day !== 1 && day !== 15) return false

    const todayIso = today.toISOString().slice(0, 10) // YYYY-MM-DD
    const { data: existing } = await fromTable('backups')
      .select('id, created_at')
      .gte('created_at', `${todayIso}T00:00:00Z`)
      .lte('created_at', `${todayIso}T23:59:59Z`)

    if (existing && existing.length > 0) {
      return false // Já foi feito um backup hoje
    }

    await createBackup('automatico')
    return true
  } catch (err) {
    console.warn('Erro ao checar backup automático quinzenal:', err)
    return false
  }
}
