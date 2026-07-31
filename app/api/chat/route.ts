import { NextRequest, NextResponse } from 'next/server'
import Groq from 'groq-sdk'
import { saveChatSession } from '@/lib/chatCache'
import { getCataCentavoClient } from '@/lib/cataCentavo'

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY || 'dummy_key_for_build' })

// Map bank_* tools to cata-centavo MCP tool names
const BANK_TOOL_MAP: Record<string, string> = {
  bank_get_accounts: 'get_accounts',
  bank_get_balance: 'get_balance',
  bank_get_transactions: 'get_transactions',
  bank_list_transactions: 'list_transactions',
  bank_get_bill_summary: 'get_bill_summary',
  bank_list_sources: 'list_sources',
  bank_set_transaction_category: 'set_transaction_category',
}

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
  // ---------------------------------------------------------------------------
  // Open Finance / Bank Tools (cata-centavo MCP)
  // ---------------------------------------------------------------------------
  {
    type: 'function',
    function: {
      name: 'bank_get_accounts',
      description: 'Lista todas as contas bancárias e cartões de crédito reais conectados via Open Finance (Pluggy), com saldos e limites. Use quando o usuário perguntar sobre extrato bancário, contas do banco, cartões reais ou saldo nas contas.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_get_balance',
      description: 'Retorna o saldo consolidado em conta corrente e limite de crédito utilizado nas contas reais do banco. Use quando perguntarem "quanto tenho no banco", saldo bancário real ou visão geral do extrato.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_get_transactions',
      description: 'Retorna o total gasto e recebido no banco num período de datas, agrupado por categoria. Use para relatórios do extrato bancário real.',
      parameters: {
        type: 'object',
        properties: {
          from: { type: 'string', description: 'Data inicial no formato YYYY-MM-DD' },
          to: { type: 'string', description: 'Data final no formato YYYY-MM-DD' },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_list_transactions',
      description: 'Lista transações bancárias individuais do extrato real (paginado). Use para listar lançamentos do extrato do banco.',
      parameters: {
        type: 'object',
        properties: {
          from: { type: 'string', description: 'Data inicial no formato YYYY-MM-DD' },
          to: { type: 'string', description: 'Data final no formato YYYY-MM-DD' },
          page: { type: 'number', description: 'Número da página (padrão: 1)' },
          pageSize: { type: 'number', description: 'Tamanho da página (padrão: 20)' },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_get_bill_summary',
      description: 'Retorna a estimativa da fatura atual dos cartões de crédito nas contas reais do banco.',
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_list_sources',
      description: 'Lista o status de sincronização das conexões bancárias da Pluggy (PicPay, Nubank, Neon, Itaú).',
    },
  },
  {
    type: 'function',
    function: {
      name: 'bank_set_transaction_category',
      description: 'Corrige a categoria de uma transação do extrato bancário real. Requer confirmação do usuário antes de executar.',
      parameters: {
        type: 'object',
        properties: {
          transactionId: { type: 'string', description: 'ID da transação bancária' },
          category: { type: 'string', description: 'Nova categoria a ser atribuída' },
        },
        required: ['transactionId', 'category'],
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

    // System prompt com distinção estrita entre despesas de planilha e extrato bancário
    const systemPrompt = `Você é o MAI Finance AI, assistente financeiro pessoal inteligente integrado ao sistema de controle de gastos e ao Open Finance (Pluggy / cata-centavo).

## Contexto atual
- **Mês exibido na tela**: ${currentMonthRef || 'desconhecido'}
- **Data/hora atual**: ${new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })}

## DISTINÇÃO IMPORTANTE DE FONTES DE DADOS
1. **Despesas Cadastradas (Planilha/Supabase)**: Lançamentos manuais feitos pelo usuário. Manipuladas via ferramentas de despesas (\`get_current_expenses\`, \`create_expense\`, etc.).
2. **Extrato Bancário Real (Open Finance / Pluggy / cata-centavo)**: Movimentação real de contas e cartões de crédito (Nubank, Itaú, Neon, PicPay). Manipuladas via ferramentas \`bank_*\` (\`bank_get_accounts\`, \`bank_get_balance\`, etc.).

Deixe SEMPRE claro na sua resposta de qual fonte os dados estão vindo (ex: "No seu extrato bancário real..." vs "Nas suas despesas cadastradas no app...").

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
  5. Quando o usuário tiver informado tudo (ou se ele mandar tudo de uma vez na mesma frase), chame a ferramenta \`create_expense\`.

- Responda SEMPRE em português do Brasil, de forma concisa, perspicaz e amigável.`

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

    // Se o modelo pediu para executar uma ferramenta
    if (message.tool_calls && message.tool_calls.length > 0) {
      const toolCall = message.tool_calls[0]
      const toolName = toolCall.function.name
      let parsedArgs: Record<string, unknown> = {}
      try {
        parsedArgs = JSON.parse(toolCall.function.arguments || '{}')
      } catch (e) {
        console.warn('Erro ao parsear argumentos da tool call do Groq:', e)
        parsedArgs = {}
      }

      // TRATAMENTO SERVER-SIDE PARA TOOLS BANCÁRIAS DE LEITURA (bank_get_*)
      if (toolName.startsWith('bank_') && toolName !== 'bank_set_transaction_category') {
        try {
          const client = await getCataCentavoClient()
          const mcpToolName = BANK_TOOL_MAP[toolName] || toolName.replace('bank_', '')
          
          const mcpResult = await client.callTool({
            name: mcpToolName,
            arguments: parsedArgs,
          })

          // Anexa a chamada e o resultado do MCP ao histórico de mensagens para a 2ª chamada ao Groq
          const secondTurnMessages: Groq.Chat.Completions.ChatCompletionMessageParam[] = [
            ...groqMessages,
            message,
            {
              role: 'tool',
              tool_call_id: toolCall.id,
              content: JSON.stringify(mcpResult.content || mcpResult),
            },
          ]

          // 2ª chamada ao Groq para sintetizar a resposta bancária em linguagem natural
          const secondCompletion = await groq.chat.completions.create({
            model: 'llama-3.3-70b-versatile',
            messages: secondTurnMessages,
            max_tokens: 2048,
            temperature: 0.3,
          })

          return NextResponse.json({
            role: 'assistant',
            content: secondCompletion.choices[0].message.content,
          })
        } catch (mcpError: unknown) {
          console.error(`Erro ao executar ferramenta bancária ${toolName}:`, mcpError)
          const errMsg = mcpError instanceof Error ? mcpError.message : 'Erro ao consultar Open Finance'
          return NextResponse.json({
            role: 'assistant',
            content: `Desculpe, ocorreu um erro ao consultar seus dados bancários no Open Finance: ${errMsg}`,
          })
        }
      }

      // Se for tool de mutação bancária (bank_set_transaction_category) ou tool de planilha (expenses)
      return NextResponse.json({
        role: 'assistant',
        content: message.content || null,
        tool_call: {
          name: toolName,
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
