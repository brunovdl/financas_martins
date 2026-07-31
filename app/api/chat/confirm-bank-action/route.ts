import { NextRequest, NextResponse } from 'next/server'
import { getCataCentavoClient } from '@/lib/cataCentavo'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { toolCall } = body

    if (!toolCall || !toolCall.name) {
      return NextResponse.json({ error: 'toolCall is required' }, { status: 400 })
    }

    if (toolCall.name !== 'bank_set_transaction_category') {
      return NextResponse.json({ error: 'Ferramenta bancária inválida para confirmação.' }, { status: 400 })
    }

    const client = await getCataCentavoClient()

    // Execute mutation tool on cata-centavo MCP
    // Mapping bank_set_transaction_category -> set_transaction_category in cata-centavo
    const mcpToolName = 'set_transaction_category'
    const result = await client.callTool({
      name: mcpToolName,
      arguments: toolCall.arguments || {},
    })

    return NextResponse.json({
      success: true,
      message: 'Categoria da transação bancária atualizada com sucesso!',
      result,
    })
  } catch (err: unknown) {
    console.error('[/api/chat/confirm-bank-action] Error:', err)
    const message = err instanceof Error ? err.message : 'Erro ao executar ação bancária'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
