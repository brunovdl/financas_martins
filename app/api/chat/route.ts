import { NextRequest, NextResponse } from 'next/server'
import Groq from 'groq-sdk'
import { saveChatSession } from '@/lib/chatCache'

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY || 'dummy_key_for_build' })

// ---------------------------------------------------------------------------
// Tool definitions (Groq tool-calling)
// ---------------------------------------------------------------------------
const tools: Groq.Chat.Completions.ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'get_current_expenses',
      description: 'Retorna todas as despesas do mês atualmente exibido na tela. Use quando o usuário pedir a lista completa de despesas.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_pending_expenses',
      description: 'Retorna apenas as despesas com status pendente do mês atualmente exibido na tela. Use quando o usuário perguntar por despesas pendentes, em aberto ou a pagar.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_expenses_by_month',
      description: 'Busca despesas de um mês específico no banco de dados (Supabase). Use quando o usuário perguntar sobre outro mês que não o atual.',
      parameters: {
        type: 'object',
        properties: {
          month_ref: {
            type: 'string',
            description: 'O mês de referência no formato YYYY-MM (ex: "2026-06" para junho de 2026)',
          },
        },
        required: ['month_ref'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_summary',
      description: 'Retorna o resumo financeiro do mês atual: total de despesas, total pago, total pendente e percentual pago.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_highest_expense',
      description: 'Retorna a despesa de maior valor do mês atualmente exibido na tela. Use quando o usuário perguntar qual o maior gasto, despesa mais cara ou maior valor.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'create_expense',
      description: 'Prepara a criação de uma nova despesa no mês atual. Requer descrição e valor em reais informados pelo usuário. Requer confirmação do usuário antes de inserir no banco.',
      parameters: {
        type: 'object',
        properties: {
          description: { type: 'string', description: 'Descrição da despesa' },
          amount: { type: 'number', description: 'Valor em reais (ex: 150.00)' },
          due_day: { type: 'number', description: 'Dia do vencimento (1-31). Padrão: 1' },
          category: { type: 'string', description: 'Categoria da despesa (ex: "outros", "internet", "energia"). Padrão: "outros"' },
          status: { type: 'string', enum: ['pendente', 'pago'], description: 'Status da despesa. Padrão: "pendente"' },
          observation: { type: 'string', description: 'Observação adicional (opcional)' },
        },
        required: ['description', 'amount'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'update_expense',
      description: 'Edita campos de uma despesa existente. Requer confirmação do usuário antes de executar.',
      parameters: {
        type: 'object',
        properties: {
          expense_id: { type: 'string', description: 'ID da despesa a ser atualizada' },
          description: { type: 'string', description: 'Nova descrição (opcional)' },
          amount: { type: 'number', description: 'Novo valor em reais (opcional)' },
          status: { type: 'string', enum: ['pendente', 'pago'], description: 'Novo status (opcional)' },
          due_day: { type: 'number', description: 'Novo dia de vencimento (opcional)' },
          category: { type: 'string', description: 'Nova categoria (opcional)' },
          observation: { type: 'string', description: 'Nova observação (opcional)' },
        },
        required: ['expense_id'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'delete_expense',
      description: 'Remove uma despesa permanentemente. Requer confirmação do usuário antes de executar.',
      parameters: {
        type: 'object',
        properties: {
          expense_id: { type: 'string', description: 'ID da despesa a ser removida' },
          description: { type: 'string', description: 'Descrição da despesa (para exibir na confirmação)' },
        },
        required: ['expense_id', 'description'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'navigate_to_month',
      description: 'Navega a interface para um mês específico.',
      parameters: {
        type: 'object',
        properties: {
          month_ref: {
            type: 'string',
            description: 'O mês de referência no formato YYYY-MM (ex: "2026-06")',
          },
        },
        required: ['month_ref'],
      },
    },
  },
]

// ---------------------------------------------------------------------------
// POST /api/chat
// ---------------------------------------------------------------------------
export async function POST(req: NextRequest) {
  try {
    if (!process.env.GROQ_API_KEY) {
      return NextResponse.json(
        { error: 'A chave GROQ_API_KEY não foi configurada no servidor (Easypanel).' },
        { status: 500 }
      )
    }

    const body = await req.json()
    const {
      messages,
      currentExpenses,
      currentMonthRef,
      categories,
      summary,
      sessionId,
    } = body

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json({ error: 'messages array is required' }, { status: 400 })
    }

    // Atualizar/Salvar histórico de sessão no servidor
    if (sessionId) {
      saveChatSession(sessionId, { messages })
    }

    // System prompt com contexto completo e instrução do fluxo passo a passo
    const systemPrompt = `Você é o MAI Finance AI, assistente financeiro pessoal inteligente integrado ao sistema de controle de gastos MAI Finance.

## Contexto atual
- **Mês exibido na tela**: ${currentMonthRef || 'desconhecido'}
- **Data/hora atual**: ${new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })}

## Despesas do mês atual (${currentMonthRef})
${currentExpenses && currentExpenses.length > 0
  ? JSON.stringify(currentExpenses, null, 2)
  : 'Nenhuma despesa carregada ainda.'}

## Categorias disponíveis
${categories && categories.length > 0
  ? categories.map((c: { id: string; name: string }) => `- ${c.id}: ${c.name}`).join('\n')
  : 'Padrão: outros'}

## Resumo financeiro atual
${summary ? JSON.stringify(summary, null, 2) : 'Não disponível.'}

## Regras estritas para criação de despesa (Fluxo Passo a Passo)
- **FLUXO INTERATIVO**: Quando o usuário pedir para criar uma despesa sem informar todos os dados (ex: "Quero cadastrar uma nova despesa" ou "Criar despesa"), responda fazendo **APENAS UMA PERGUNTA DE CADA VEZ** de maneira amigável:
  1. Pergunta **apenas** a **Descrição** (ex: "Vamos cadastrar uma nova despesa! 📝 Qual é o nome ou descrição da despesa?")
  2. Quando o usuário responder a descrição, confirme e pergunte **apenas** o **Valor** em R$ (ex: "Legal! Qual o valor em reais (R$) para [Descrição]?")
  3. Quando o usuário responder o valor, confirme e pergunte **apenas** o **Dia de vencimento** (ex: "Entendido. Qual o dia de vencimento (1 a 31)?")
  4. Quando o usuário responder o dia, peça a **Categoria** (ex: "Anotado! Qual é a categoria da despesa?")
  5. Quando o usuário tiver informado tudo (ou se ele mandar tudo de uma vez na mesma frase, ex: "Criar despesa de internet R$ 150 dia 10 em outros"), chame a ferramenta \`create_expense\`.

- NUNCA liste todos os campos de uma vez nem faça uma lista longa de categorias de uma vez só no chat.
- **REGRA DE CONFIRMAÇÃO E ENCERRAMENTO**:
  1. TODAS as mutações (criar, editar, deletar) exigem confirmação via botão antes da inserção.
  2. Assim que uma despesa for criada (mensagem "criada com sucesso" ou tool call executada), o fluxo de criação está **TOTALMENTE ENCERRADO**.
  3. Se o usuário mandar qualquer mensagem que NÃO seja continuar o cadastro (ex: "Preciso de um plano para reduzir gastos", "Qual meu maior gasto?", "Tenho renda de R$ 18.000"), NUNCA tente cadastrar uma nova despesa ou chamar \`create_expense\`. Responda à dúvida do usuário normalmente como um consultor financeiro perspicaz!
- Responda SEMPRE em português do Brasil, de forma concisa e amigável.`

    const groqMessages: Groq.Chat.Completions.ChatCompletionMessageParam[] = [
      { role: 'system', content: systemPrompt },
      ...messages,
    ]

    let completion
    try {
      completion = await groq.chat.completions.create({
        model: 'llama-3.3-70b-versatile',
        messages: groqMessages,
        tools,
        tool_choice: 'auto',
        max_tokens: 2048,
        temperature: 0.3,
      })
    } catch (groqErr) {
      console.warn('Tentativa com ferramentas falhou no Groq, executando fallback sem tools:', groqErr)
      completion = await groq.chat.completions.create({
        model: 'llama-3.3-70b-versatile',
        messages: groqMessages,
        max_tokens: 2048,
        temperature: 0.3,
      })
    }

    const choice = completion.choices[0]
    const message = choice.message

    // Se o modelo quer chamar uma tool, retorna o tool_call com parsing seguro de JSON
    if (message.tool_calls && message.tool_calls.length > 0) {
      const toolCall = message.tool_calls[0]
      let parsedArgs: Record<string, unknown> = {}
      try {
        parsedArgs = JSON.parse(toolCall.function.arguments || '{}')
      } catch (e) {
        console.warn('Erro ao parsear argumentos da tool call do Groq:', e)
        parsedArgs = {}
      }

      return NextResponse.json({
        role: 'assistant',
        content: message.content || null,
        tool_call: {
          name: toolCall.function.name,
          arguments: parsedArgs,
          id: toolCall.id,
        },
      })
    }

    // Resposta de texto normal
    return NextResponse.json({
      role: 'assistant',
      content: message.content,
    })
  } catch (err: unknown) {
    console.error('[/api/chat] Error:', err)
    const message = err instanceof Error ? err.message : 'Erro interno do servidor'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
