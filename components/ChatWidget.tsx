'use client'

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { X, Send, Bot, Sparkles, Check, AlertTriangle, Trash2 } from 'lucide-react'
import type { ThemeTokens, CategoryTheme } from '@/lib/theme'
import { formatBRL, monthLabel } from '@/lib/theme'
import type { UIExpense } from './GastosApp'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  toolCall?: ToolCall
  pendingConfirmation?: PendingAction
  isLoading?: boolean
}

interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  id: string
}

interface PendingAction {
  type: 'create' | 'update' | 'delete'
  toolCall: ToolCall
  label: string
}

interface ChatWidgetProps {
  T: ThemeTokens
  theme: 'dark' | 'light'
  expenses: UIExpense[]
  monthRef: string
  categoriesList: CategoryTheme[]
  isSupabaseActive: boolean
  onCreateExpense: (data: {
    description: string
    amount: number
    dueDay: number
    category: string
    status: 'pendente' | 'pago'
    observation: string
  }) => Promise<void>
  onUpdateExpense: (id: string, field: keyof UIExpense, value: unknown) => Promise<void>
  onDeleteExpense: (id: string) => Promise<void>
  onNavigateToMonth: (monthRef: string) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function msgId() {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

function MonthExpensesTable({ expenses, categoriesList, T }: {
  expenses: UIExpense[]
  categoriesList: CategoryTheme[]
  T: ThemeTokens
}) {
  if (expenses.length === 0) return (
    <p className="text-xs italic" style={{ color: T.textFaint }}>Nenhuma despesa encontrada.</p>
  )
  return (
    <div className="space-y-1.5 mt-2">
      {expenses.map((e) => {
        const cat = categoriesList.find(c => c.id === e.category)
        return (
          <div key={e.id} className="flex items-center justify-between gap-2 text-xs rounded-lg px-2.5 py-1.5"
            style={{ backgroundColor: `${T.border}50` }}>
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: cat?.dark || T.textFaint }} />
              <span className="truncate font-medium" style={{ color: T.textPrimary }}>{e.description}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${e.status === 'pago' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                {e.status}
              </span>
              <span className="font-mono text-xs font-semibold" style={{ color: T.textPrimary }}>{formatBRL(e.amount)}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function ChatWidget({
  T,
  theme,
  expenses,
  monthRef,
  categoriesList,
  isSupabaseActive,
  onCreateExpense,
  onUpdateExpense,
  onDeleteExpense,
  onNavigateToMonth,
}: ChatWidgetProps) {
  const [sessionId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('mai_chat_session_id')
      if (!id) {
        id = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        sessionStorage.setItem('mai_chat_session_id', id)
      }
      return id
    }
    return `session-${Date.now()}`
  })
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: msgId(),
      role: 'assistant',
      content: `Olá! Sou o **MAI Finance AI** 🤖\n\nPosso te ajudar a:\n- Consultar e analisar suas despesas\n- Criar novas despesas passo a passo\n- Marcar despesas como pagas ou pendentes\n- Dar insights sobre seus gastos\n\nO que você gostaria de fazer?`,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Compute summary for context
  const summary = useMemo(() => {
    const monthExpenses = expenses.filter(e => e.monthRef === monthRef)
    return {
      monthRef,
      total: monthExpenses.reduce((s, e) => s + e.amount, 0),
      paid: monthExpenses.filter(e => e.status === 'pago').reduce((s, e) => s + e.amount, 0),
      pending: monthExpenses.filter(e => e.status === 'pendente').reduce((s, e) => s + e.amount, 0),
      count: monthExpenses.length,
      countPending: monthExpenses.filter(e => e.status === 'pendente').length,
    }
  }, [expenses, monthRef])

  // ---------------------------------------------------------------------------
  // Tool execution (client-side)
  // ---------------------------------------------------------------------------
  const executeTool = useCallback(async (
    toolCall: ToolCall,
    confirmed = false
  ): Promise<{ content: string; pendingAction?: PendingAction; inlineExpenses?: UIExpense[] }> => {
    const args = toolCall.arguments

    switch (toolCall.name) {
      case 'get_current_expenses': {
        const statusFilter = args.status as 'pendente' | 'pago' | undefined
        let current = expenses.filter(e => e.monthRef === monthRef)
        if (statusFilter) {
          current = current.filter(e => e.status === statusFilter)
        }
        const statusLabel = statusFilter ? ` ${statusFilter}s` : ''
        return {
          content: `Encontrei **${current.length} despesas${statusLabel}** em ${monthLabel(monthRef)}:`,
          inlineExpenses: current,
        }
      }

      case 'get_pending_expenses': {
        const pending = expenses.filter(e => e.monthRef === monthRef && e.status === 'pendente')
        return {
          content: pending.length > 0
            ? `Encontrei **${pending.length} despesas pendentes** em ${monthLabel(monthRef)}:`
            : `Não há despesas pendentes registradas para ${monthLabel(monthRef)}.`,
          inlineExpenses: pending.length > 0 ? pending : undefined,
        }
      }

      case 'get_expenses_by_month': {
        const targetMonth = args.month_ref as string
        const statusFilter = args.status as 'pendente' | 'pago' | undefined
        let list: UIExpense[] = []

        if (!isSupabaseActive) {
          list = expenses.filter(e => e.monthRef === targetMonth)
        } else {
          try {
            const res = await fetch(`/api/expenses-by-month?month=${targetMonth}`)
            if (res.ok) {
              list = await res.json()
            } else {
              list = expenses.filter(e => e.monthRef === targetMonth)
            }
          } catch {
            list = expenses.filter(e => e.monthRef === targetMonth)
          }
        }

        if (statusFilter) {
          list = list.filter(e => e.status === statusFilter)
        }
        const statusLabel = statusFilter ? ` ${statusFilter}s` : ''

        return {
          content: list.length > 0
            ? `Encontrei **${list.length} despesas${statusLabel}** em ${monthLabel(targetMonth)}:`
            : `Não há despesas${statusLabel} registradas para ${monthLabel(targetMonth)}.`,
          inlineExpenses: list.length > 0 ? list : undefined,
        }
      }

      case 'get_summary': {
        const pct = summary.total > 0 ? (summary.paid / summary.total * 100).toFixed(1) : '0.0'
        return {
          content: `📊 **Resumo de ${monthLabel(monthRef)}**\n\n💰 Total: **${formatBRL(summary.total)}**\n✅ Pago: **${formatBRL(summary.paid)}** (${pct}%)\n⏳ Pendente: **${formatBRL(summary.pending)}**\n📋 ${summary.count} lançamentos, ${summary.countPending} pendentes`,
        }
      }

      case 'get_highest_expense': {
        const current = expenses.filter(e => e.monthRef === monthRef)
        if (current.length === 0) {
          return { content: `Não há despesas cadastradas em **${monthLabel(monthRef)}**.` }
        }
        const highest = current.reduce((prev, curr) => (curr.amount > prev.amount ? curr : prev), current[0])
        const cat = categoriesList.find(c => c.id === highest.category)
        return {
          content: `🏆 A maior despesa de **${monthLabel(monthRef)}** é **"${highest.description}"** no valor de **${formatBRL(highest.amount)}** (Categoria: ${cat?.name || 'Outros'}, Status: ${highest.status}).`,
          inlineExpenses: [highest],
        }
      }

      case 'create_expense': {
        const description = (args.description as string) || 'Nova despesa'
        const amount = Number(args.amount) || 0
        const dueDay = Math.min(31, Math.max(1, Number(args.due_day) || 1))
        const catId = (args.category as string | undefined)?.toLowerCase().replace(/\s+/g, '-') || 'outros'
        const validCat = categoriesList.find(c => c.id === catId || c.name.toLowerCase() === (args.category as string || '').toLowerCase())
        const catName = validCat?.name || 'Outros'

        if (!confirmed) {
          return {
            content: `Deseja cadastrar a seguinte nova despesa em **${monthLabel(monthRef)}**?\n\n📝 **Descrição:** ${description}\n💰 **Valor:** ${formatBRL(amount)}\n📅 **Vencimento:** Dia ${dueDay}\n🏷️ **Categoria:** ${catName}`,
            pendingAction: {
              type: 'create',
              toolCall,
              label: `Criar "${description}"`,
            },
          }
        }

        await onCreateExpense({
          description,
          amount,
          dueDay,
          category: validCat?.id || 'outros',
          status: (args.status as 'pendente' | 'pago') || 'pendente',
          observation: (args.observation as string) || '',
        })
        return {
          content: `✅ Despesa **"${description}"** no valor de **${formatBRL(amount)}** criada com sucesso em ${monthLabel(monthRef)}!`,
        }
      }

      case 'update_expense': {
        if (!confirmed) {
          const target = expenses.find(e => e.id === args.expense_id || e.dbId === args.expense_id)
          const name = target?.description || `despesa ${args.expense_id}`
          const changes = Object.entries(args)
            .filter(([k]) => k !== 'expense_id')
            .map(([k, v]) => {
              if (k === 'amount') return `valor → ${formatBRL(v as number)}`
              if (k === 'status') return `status → ${v}`
              if (k === 'due_day') return `vencimento → dia ${v}`
              if (k === 'description') return `descrição → "${v}"`
              if (k === 'category') return `categoria → ${v}`
              if (k === 'observation') return `observação → "${v}"`
              return `${k} → ${v}`
            })
            .join(', ')
          return {
            content: `Deseja atualizar **"${name}"** com as seguintes alterações?\n${changes}`,
            pendingAction: { type: 'update', toolCall, label: `Atualizar "${name}"` },
          }
        }
        // Confirmed — execute
        const expId = args.expense_id as string
        const fields: Array<{ field: keyof UIExpense; value: unknown }> = []
        if (args.description !== undefined) fields.push({ field: 'description', value: args.description })
        if (args.amount !== undefined) fields.push({ field: 'amount', value: args.amount })
        if (args.status !== undefined) fields.push({ field: 'status', value: args.status })
        if (args.due_day !== undefined) fields.push({ field: 'dueDay', value: args.due_day })
        if (args.category !== undefined) {
          const cat = categoriesList.find(c => c.id === (args.category as string) || c.name.toLowerCase() === (args.category as string).toLowerCase())
          fields.push({ field: 'category', value: cat?.id || 'outros' })
        }
        if (args.observation !== undefined) fields.push({ field: 'observation', value: args.observation })
        for (const { field, value } of fields) {
          await onUpdateExpense(expId, field, value)
        }
        return { content: `✅ Despesa atualizada com sucesso!` }
      }

      case 'delete_expense': {
        if (!confirmed) {
          return {
            content: `⚠️ Você tem certeza que deseja **excluir** a despesa **"${args.description}"**? Esta ação não pode ser desfeita.`,
            pendingAction: {
              type: 'delete',
              toolCall,
              label: `Excluir "${args.description}"`,
            },
          }
        }
        await onDeleteExpense(args.expense_id as string)
        return { content: `🗑️ Despesa **"${args.description}"** excluída com sucesso.` }
      }

      case 'navigate_to_month': {
        const target = args.month_ref as string
        onNavigateToMonth(target)
        return { content: `📅 Navegando para **${monthLabel(target)}**...` }
      }

      case 'bank_set_transaction_category': {
        const { transactionId, category } = args as { transactionId: string; category: string }
        if (!confirmed) {
          return {
            content: `Deseja alterar a categoria da transação bancária **"${transactionId}"** para **"${category}"** no Open Finance?`,
            pendingAction: {
              type: 'update',
              toolCall,
              label: `Confirmar categoria "${category}"`,
            },
          }
        }

        const res = await fetch('/api/chat/confirm-bank-action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ toolCall }),
        })
        const resData = await res.json()
        if (!res.ok || resData.error) {
          throw new Error(resData.error || 'Falha ao atualizar categoria da transação bancária.')
        }

        return {
          content: `✅ Categoria da transação bancária atualizada para **"${category}"** com sucesso!`,
        }
      }

      default:
        return { content: 'Ferramenta desconhecida.' }
    }
  }, [expenses, monthRef, summary, categoriesList, isSupabaseActive, onCreateExpense, onUpdateExpense, onDeleteExpense, onNavigateToMonth])

  // ---------------------------------------------------------------------------
  // Send message
  // ---------------------------------------------------------------------------
  const sendMessage = useCallback(async (userInput: string) => {
    if (!userInput.trim() || isLoading) return

    const userMsg: ChatMessage = { id: msgId(), role: 'user', content: userInput }
    const loadingMsg: ChatMessage = { id: msgId(), role: 'assistant', content: '', isLoading: true }

    setMessages(prev => [...prev, userMsg, loadingMsg])
    setInput('')
    setIsLoading(true)

    try {
      // Build message history for the API (exclude loading and system messages)
      const historyForApi = [...messages, userMsg]
        .filter(m => !m.isLoading && m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content || '' }))

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: historyForApi,
          currentExpenses: expenses.filter(e => e.monthRef === monthRef),
          currentMonthRef: monthRef,
          categories: categoriesList.map(c => ({ id: c.id, name: c.name })),
          summary,
          sessionId,
        }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()

      if (data.error) {
        throw new Error(data.error)
      }

      // If model wants to call a tool, execute it client-side
      if (data.tool_call) {
        const result = await executeTool(data.tool_call)
        const assistantMsg: ChatMessage = {
          id: msgId(),
          role: 'assistant',
          content: result.content,
          pendingConfirmation: result.pendingAction,
          toolCall: result.pendingAction ? data.tool_call : undefined,
        }
        // If there are inline expenses to display, add them
        if (result.inlineExpenses) {
          (assistantMsg as ChatMessage & { inlineExpenses?: UIExpense[] }).inlineExpenses = result.inlineExpenses
        }
        setMessages(prev => [...prev.filter(m => !m.isLoading), assistantMsg])
      } else {
        // Plain text response
        setMessages(prev => [
          ...prev.filter(m => !m.isLoading),
          { id: msgId(), role: 'assistant', content: data.content || 'Sem resposta.' },
        ])
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Erro desconhecido'
      setMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        {
          id: msgId(),
          role: 'assistant',
          content: `❌ Ocorreu um erro ao processar sua mensagem: ${errMsg}. Verifique sua conexão e tente novamente.`,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, messages, expenses, monthRef, categoriesList, summary, sessionId, executeTool])

  // ---------------------------------------------------------------------------
  // Confirm / Cancel pending actions
  // ---------------------------------------------------------------------------
  const handleConfirm = useCallback(async (msgId_: string, toolCall: ToolCall) => {
    setIsLoading(true)
    const loadingMsg: ChatMessage = { id: msgId(), role: 'assistant', content: '', isLoading: true }
    setMessages(prev => [...prev.map(m => m.id === msgId_ ? { ...m, pendingConfirmation: undefined } : m), loadingMsg])

    try {
      const result = await executeTool(toolCall, true)
      setMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        { id: msgId(), role: 'assistant', content: result.content },
      ])
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Erro'
      setMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        { id: msgId(), role: 'assistant', content: `❌ Erro ao executar ação: ${errMsg}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [executeTool])

  const handleCancel = useCallback((msgId_: string) => {
    setMessages(prev => prev.map(m =>
      m.id === msgId_
        ? { ...m, pendingConfirmation: undefined, content: m.content + '\n\n_Ação cancelada._' }
        : m
    ))
  }, [])

  // ---------------------------------------------------------------------------
  // Render markdown-lite (bold + line breaks)
  // ---------------------------------------------------------------------------
  function renderContent(text: string) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      return <span key={i}>{part.split('\n').map((line, j, arr) => (
        <React.Fragment key={j}>{line}{j < arr.length - 1 && <br />}</React.Fragment>
      ))}</span>
    })
  }

  // ---------------------------------------------------------------------------
  // Design Direction Summary (Frontend Skill)
  // Aesthetic: "Precision Dark Terminal" — inspired by financial data terminals
  // DFII: Impact(5) + Fit(5) + Feasibility(4) + Performance(4) - Risk(2) = 16 → capped at 15 (Excellent)
  // Differentiator: Pulsing gradient FAB, monochrome chat surface with accent-only color highlights,
  //   inline expense tables inside messages — feels like a Bloomberg terminal chat, not a generic AI widget.
  // ---------------------------------------------------------------------------

  const accentGradient = `linear-gradient(135deg, ${T.accent}, ${T.accentTo})`

  return (
    <>
      {/* FAB */}
      <button
        onClick={() => setIsOpen(v => !v)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 active:scale-95 cursor-pointer"
        style={{
          background: accentGradient,
          boxShadow: `0 0 32px -4px ${T.accent}80, 0 8px 24px -4px rgba(0,0,0,0.5)`,
        }}
        aria-label="Abrir assistente de IA"
        title="MAI Finance AI"
      >
        {isOpen
          ? <X size={22} style={{ color: T.accentOnBrand }} />
          : (
            <div className="relative">
              <Bot size={22} style={{ color: T.accentOnBrand }} />
              <span
                className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 animate-pulse"
                style={{ backgroundColor: T.accent === '#3FD6C4' ? '#22d3ee' : T.accent, borderColor: 'transparent' }}
              />
            </div>
          )
        }
      </button>

      {/* Floating Chat Popover Modal */}
      {isOpen && (
        <div
          className="fixed z-40 flex flex-col transition-all duration-300 ease-out shadow-2xl rounded-2xl border overflow-hidden bottom-24 right-3 left-3 sm:left-auto sm:right-6 sm:w-[400px] h-[560px] max-h-[calc(100vh-120px)]"
          style={{
            backgroundColor: theme === 'dark' ? '#0E1220' : '#F8F9FC',
            borderColor: T.border,
            boxShadow: theme === 'dark'
              ? `0 20px 50px -10px rgba(0,0,0,0.8), 0 0 1px 1px ${T.border}`
              : `0 20px 40px -10px rgba(0,0,0,0.15), 0 0 1px 1px ${T.border}`,
          }}
        >
          <div className="flex flex-col h-full w-full">
            {/* Header */}
            <div
              className="flex items-center justify-between px-4 py-3.5 border-b flex-shrink-0"
              style={{
                borderColor: T.border,
                background: theme === 'dark'
                  ? `linear-gradient(135deg, #131A30, #0E1220)`
                  : `linear-gradient(135deg, #F0F4FF, #F8F9FC)`,
              }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: accentGradient, boxShadow: `0 0 16px -4px ${T.accent}60` }}
                >
                  <Sparkles size={16} style={{ color: T.accentOnBrand }} />
                </div>
                <div>
                  <h2 className="text-sm font-semibold tracking-tight" style={{ color: T.textPrimary }}>
                    MAI Finance AI
                  </h2>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[10px] font-mono" style={{ color: T.textFaint }}>
                      llama-3.3-70b · {isSupabaseActive ? 'online' : 'local'}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-lg transition-all cursor-pointer"
                style={{ color: T.textFaint }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = T.rowHover)}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                aria-label="Fechar chat"
              >
                <X size={16} />
              </button>
            </div>

            {/* Context pill */}
            <div
              className="px-4 py-2 flex items-center gap-2 border-b flex-shrink-0"
              style={{ borderColor: T.border, backgroundColor: `${T.surface}` }}
            >
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full border"
                style={{ color: T.accent, borderColor: `${T.accent}40`, backgroundColor: `${T.accent}10` }}>
                {monthLabel(monthRef)}
              </span>
              <span className="text-[10px]" style={{ color: T.textFaint }}>
                {expenses.filter(e => e.monthRef === monthRef).length} despesas · {formatBRL(summary.pending)} pendente
              </span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {messages.map((msg) => {
                const isUser = msg.role === 'user'
                const inlineExps = (msg as ChatMessage & { inlineExpenses?: UIExpense[] }).inlineExpenses

                return (
                  <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2`}>
                    {!isUser && (
                      <div
                        className="w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
                        style={{ background: accentGradient }}
                      >
                        <Bot size={13} style={{ color: T.accentOnBrand }} />
                      </div>
                    )}

                    <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1.5`}>
                      {/* Message bubble */}
                      {(msg.content || msg.isLoading) && (
                        <div
                          className="rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed"
                          style={
                            isUser
                              ? { background: accentGradient, color: T.accentOnBrand }
                              : {
                                backgroundColor: theme === 'dark' ? '#161C2E' : '#FFFFFF',
                                color: T.textPrimary,
                                border: `1px solid ${T.border}`,
                              }
                          }
                        >
                          {msg.isLoading
                            ? (
                              <div className="flex items-center gap-1.5 py-0.5">
                                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: T.accent, animationDelay: '0ms' }} />
                                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: T.accent, animationDelay: '150ms' }} />
                                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: T.accent, animationDelay: '300ms' }} />
                              </div>
                            )
                            : renderContent(msg.content)
                          }
                        </div>
                      )}

                      {/* Category selector chips when assistant explicitly asks for category selection */}
                      {!isUser && msg.content && !msg.pendingConfirmation && !msg.content.includes('criada com sucesso') && !msg.content.includes('Deseja cadastrar') && !msg.content.includes('Ação cancelada') && (msg.content.toLowerCase().includes('qual é a categoria') || msg.content.toLowerCase().includes('qual a categoria') || msg.content.toLowerCase().includes('escolha uma categoria') || msg.content.toLowerCase().includes('qual é a categoria da despesa')) && (
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {categoriesList.map((cat) => (
                            <button
                              key={cat.id}
                              onClick={() => sendMessage(cat.name)}
                              disabled={isLoading}
                              className="text-[11px] px-2.5 py-1 rounded-full border transition-all active:scale-95 cursor-pointer font-medium disabled:opacity-50"
                              style={{
                                backgroundColor: `${cat.dark}18`,
                                borderColor: `${cat.dark}50`,
                                color: cat.dark,
                              }}
                            >
                              🏷️ {cat.name}
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Inline expenses table */}
                      {inlineExps && inlineExps.length > 0 && (
                        <div
                          className="w-full rounded-xl border px-3 py-2.5"
                          style={{
                            backgroundColor: theme === 'dark' ? '#0F1525' : '#F8FAFF',
                            borderColor: T.border,
                          }}
                        >
                          <MonthExpensesTable expenses={inlineExps} categoriesList={categoriesList} T={T} />
                        </div>
                      )}

                      {/* Confirmation buttons */}
                      {msg.pendingConfirmation && msg.toolCall && (
                        <div className="flex items-center gap-2 mt-1">
                          <button
                            onClick={() => handleConfirm(msg.id, msg.toolCall!)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all active:scale-95 cursor-pointer"
                            style={{
                              backgroundColor: msg.pendingConfirmation.type === 'delete'
                                ? T.danger
                                : msg.pendingConfirmation.type === 'create'
                                ? T.success
                                : T.accent,
                              color: msg.pendingConfirmation.type === 'delete' ? '#FFFFFF' : T.accentOnBrand,
                            }}
                          >
                            {msg.pendingConfirmation.type === 'delete'
                              ? <><Trash2 size={11} /> Excluir</>
                              : msg.pendingConfirmation.type === 'create'
                              ? <><Check size={11} /> Confirmar Criação</>
                              : <><Check size={11} /> Confirmar Edição</>
                            }
                          </button>
                          <button
                            onClick={() => handleCancel(msg.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all active:scale-95 cursor-pointer border"
                            style={{ color: T.textMuted, borderColor: T.border, backgroundColor: 'transparent' }}
                          >
                            Cancelar
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick actions */}
            <div
              className="px-4 py-2 border-t flex gap-2 overflow-x-auto flex-shrink-0 scrollbar-hide"
              style={{ borderColor: T.border }}
            >
              {[
                { label: '📊 Resumo do mês', query: 'Qual é o resumo financeiro deste mês?' },
                { label: '⏳ Despesas pendentes', query: 'Quais despesas estão pendentes neste mês?' },
                { label: '🔝 Maior gasto', query: 'Qual é a maior despesa deste mês?' },
                { label: '➕ Criar despesa', query: 'Quero cadastrar uma nova despesa' },
              ].map(({ label, query }) => (
                <button
                  key={label}
                  onClick={() => sendMessage(query)}
                  disabled={isLoading}
                  className="flex-shrink-0 flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-full border transition-all cursor-pointer whitespace-nowrap disabled:opacity-50"
                  style={{
                    color: T.accent,
                    borderColor: `${T.accent}40`,
                    backgroundColor: `${T.accent}08`,
                  }}
                  onMouseEnter={e => !isLoading && (e.currentTarget.style.backgroundColor = `${T.accent}18`)}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = `${T.accent}08`)}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Warning if no API connection */}
            {!isSupabaseActive && (
              <div className="px-4 py-2 flex items-center gap-2 border-t flex-shrink-0"
                style={{ borderColor: T.border, backgroundColor: `${T.warning}08` }}>
                <AlertTriangle size={12} style={{ color: T.warning }} />
                <span className="text-[10px]" style={{ color: T.warning }}>
                  Supabase offline — mudanças salvas apenas localmente
                </span>
              </div>
            )}

            {/* Input area */}
            <div
              className="p-3 border-t flex-shrink-0"
              style={{ borderColor: T.border }}
            >
              <div
                className="flex items-end gap-2 rounded-xl border px-3 py-2 transition-all"
                style={{
                  backgroundColor: theme === 'dark' ? '#0A0D18' : '#FFFFFF',
                  borderColor: T.border,
                }}
                onFocus={() => {}}
              >
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage(input)
                    }
                  }}
                  placeholder="Pergunte sobre seus gastos..."
                  rows={1}
                  disabled={isLoading}
                  className="flex-1 resize-none outline-none bg-transparent text-xs leading-relaxed disabled:opacity-60 max-h-28"
                  style={{ color: T.textPrimary, fontFamily: 'inherit' }}
                />
                <button
                  onClick={() => sendMessage(input)}
                  disabled={!input.trim() || isLoading}
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-all active:scale-95 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ background: accentGradient }}
                  aria-label="Enviar mensagem"
                >
                  <Send size={12} style={{ color: T.accentOnBrand }} />
                </button>
              </div>
              <p className="text-[9px] text-center mt-1.5" style={{ color: T.textFaint }}>
                Enter para enviar · Shift+Enter para nova linha
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}


