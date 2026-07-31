import { NextRequest, NextResponse } from 'next/server'
import { fetchExpenses as fetchSupabaseExpenses } from '@/lib/supabaseClient'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const month = searchParams.get('month')
    if (!month || !/^\d{4}-\d{2}$/.test(month)) {
      return NextResponse.json({ error: 'Valid month parameter (YYYY-MM) is required' }, { status: 400 })
    }

    const dbExps = await fetchSupabaseExpenses(month)
    const formatted = dbExps.map((e) => {
      let dueDay = 1
      if (e.due_date) {
        const parts = e.due_date.split('-')
        if (parts.length >= 3) {
          const parsed = parseInt(parts[2], 10)
          if (!isNaN(parsed) && parsed >= 1 && parsed <= 31) dueDay = parsed
        }
      }

      return {
        id: e.id,
        monthRef: month,
        dueDay,
        category: e.category?.name?.toLowerCase().replace(/\s+/g, '-') || 'outros',
        description: e.description,
        amount: typeof e.amount === 'number' ? e.amount : parseFloat(String(e.amount)) || 0,
        paymentDay: e.payment_date || '',
        status: e.status,
        observation: e.observation || '',
      }
    })

    return NextResponse.json(formatted)
  } catch (err: unknown) {
    console.error('[/api/expenses-by-month] Error:', err)
    return NextResponse.json([], { status: 200 })
  }
}
