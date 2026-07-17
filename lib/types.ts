export type ExpenseStatus = 'pago' | 'pendente'

export interface Category {
  id: string
  name: string
  color: string         // hex base — variante claro/escuro resolvida no frontend
  color_hex?: string
  created_at: string
}

export interface Expense {
  id: string
  due_date: string       // ISO date: "2026-04-05"
  category_id: string | null
  description: string
  amount: number
  payment_date: string | null
  status: ExpenseStatus
  observation: string | null
  month_ref: string      // ISO date primeiro dia do mês: "2026-04-01"
  created_at: string
  updated_at: string
  // join via select('*, category:categories(*)')
  category?: Category
}

export interface MonthlySummary {
  month_ref: string
  total_despesas: number
  total_pendente: number
  qtd_pendente: number
}

// Payload de criação — sem campos gerados pelo banco
export type NewExpense = Omit<Expense, 'id' | 'created_at' | 'updated_at' | 'category'>
export type PatchExpense = Partial<Omit<Expense, 'id' | 'created_at' | 'updated_at' | 'category'>>

export type NewCategory = Pick<Category, 'name' | 'color'>
