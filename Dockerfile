# ============================================================
# Stage 1: deps — instala dependências
# ============================================================
FROM node:22-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# ============================================================
# Stage 2: builder — compila o projeto Next.js
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Variáveis de ambiente públicas do Supabase (injetadas em build-time)
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY

ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

# Ativa o output standalone para imagem menor
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ============================================================
# Stage 3: runner — imagem final mínima para produção
# ============================================================
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Cria usuário não-root por segurança e diretório de dados persistentes do cata-centavo
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    mkdir -p /data/cata-centavo && \
    chown -R nextjs:nodejs /data/cata-centavo

# Copia arquivos standalone do Next.js
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copia manualmente módulos invocados via child_process (cata-centavo MCP server)
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/cata-centavo ./node_modules/cata-centavo
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/@modelcontextprotocol ./node_modules/@modelcontextprotocol
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/pluggy-sdk ./node_modules/pluggy-sdk
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/pino ./node_modules/pino
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/pino-roll ./node_modules/pino-roll
COPY --from=builder --chown=nextjs:nodejs /app/node_modules/zod ./node_modules/zod

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
