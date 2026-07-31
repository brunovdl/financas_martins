// ---------------------------------------------------------------------------
// Memory Session Cache with 20-Minute TTL
// ---------------------------------------------------------------------------

export interface ChatSessionData {
  sessionId: string
  lastActiveAt: number
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>
  creationDraft?: {
    step: 'description' | 'amount' | 'due_day' | 'category' | 'confirm'
    description?: string
    amount?: number
    due_day?: number
    category?: string
  }
}

const TTL_MS = 20 * 60 * 1000 // 20 minutos

const globalForCache = globalThis as unknown as {
  chatSessions?: Map<string, ChatSessionData>
}

const sessions = globalForCache.chatSessions ?? new Map<string, ChatSessionData>()

if (process.env.NODE_ENV !== 'production') {
  globalForCache.chatSessions = sessions
}

// Limpeza automática de sessões expiradas a cada 5 minutos
if (typeof setInterval !== 'undefined') {
  setInterval(() => {
    const now = Date.now()
    for (const [id, session] of Array.from(sessions.entries())) {
      if (now - session.lastActiveAt > TTL_MS) {
        sessions.delete(id)
      }
    }
  }, 5 * 60 * 1000)
}

export function getChatSession(sessionId: string): ChatSessionData | null {
  const session = sessions.get(sessionId)
  if (!session) return null

  // Verificar expiração
  if (Date.now() - session.lastActiveAt > TTL_MS) {
    sessions.delete(sessionId)
    return null
  }

  // Atualizar timestamp de atividade
  session.lastActiveAt = Date.now()
  return session
}

export function saveChatSession(sessionId: string, data: Partial<ChatSessionData>): ChatSessionData {
  const existing = getChatSession(sessionId)
  const updated: ChatSessionData = {
    sessionId,
    lastActiveAt: Date.now(),
    messages: data.messages ?? existing?.messages ?? [],
    creationDraft: data.creationDraft !== undefined ? data.creationDraft : existing?.creationDraft,
  }

  sessions.set(sessionId, updated)
  return updated
}

export function clearChatSession(sessionId: string): void {
  sessions.delete(sessionId)
}
