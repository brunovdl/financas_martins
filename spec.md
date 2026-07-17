# Spec — App de Controle de Gastos (MAI Finance)

## 1. Visão geral

Substituir a planilha Google Sheets (uma aba por mês) por uma aplicação web
conectada ao Supabase, mantendo a mesma facilidade de leitura rápida por
cores/status, com um visual moderno, tema claro/escuro e uma visão
consolidada do mês.

**Problema atual:** cada mês vira uma nova aba na planilha, dificultando
histórico, buscas e evolução ao longo do tempo.

**Solução:** um único banco de despesas filtrável por mês (`month_ref`),
com dashboard de resumo, edição inline, alternância de tema e
sincronização em tempo real.

---

## 2. Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript |
| Estilo | Tailwind CSS + tokens de tema via JS (objeto `THEMES`) |
| Backend | Supabase (Postgres + Auth + Realtime) |
| Ícones | lucide-react |
| Tipografia | Outfit (títulos) · Inter (corpo) · JetBrains Mono (números/datas) |
| Deploy sugerido | Vercel |

---

## 3. Modelo de dados (Supabase)

### `categories`
| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid, PK | |
| name | text, unique | Ex: Outros, DAAE, CondInvest, Imposto, Caixa, CPFL |
| color | text (hex) | Cor base da tag (variantes claro/escuro resolvidas no frontend) |
| created_at | timestamptz | |

### `expenses`
| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid, PK | |
| due_date | date | Vencimento |
| category_id | uuid, FK → categories | |
| description | text | Descrição |
| amount | numeric(12,2) | Valor |
| payment_date | date, nullable | Data em que foi pago |
| status | enum: `pago` \| `pendente` | |
| observation | text, nullable | Ex: link de matrícula, chave Pix |
| month_ref | date | Primeiro dia do mês de referência (`2026-04-01`) — substitui a lógica de "aba por mês" |
| created_at / updated_at | timestamptz | |

### View `monthly_summary`
Agregado por `month_ref`: `total_despesas`, `total_pendente`, `qtd_pendente`.
Alimenta os cards de resumo sem precisar recalcular no cliente.

### RLS
Single-user por padrão (`auth.role() = 'authenticated'` tem acesso total a
`expenses` e `categories`). Ajustar se o app for multiusuário.

> Schema completo e seed das categorias: `schema.sql` (já entregue).

---

## 4. Funcionalidades

### 4.1 Navegação por mês
- Seletor com setas ◀ / ▶ trocando `month_ref`
- Substitui a criação de abas — todo o histórico fica no mesmo banco,
  navegável e pesquisável entre meses

### 4.2 Tema claro/escuro
- Botão de sol/lua no header alterna `theme` (`dark` | `light`)
- Todas as cores (fundo, superfícies, texto, categorias, status) vêm de
  um objeto de tokens único (`THEMES.dark` / `THEMES.light`), sem cores
  soltas espalhadas pelo componente
- Categorias e status (pago/pendente) usam tonalidades diferentes por
  tema — no claro, tons mais escuros e saturados pra manter contraste
  em fundo branco, em vez de só reduzir o brilho do fundo

### 4.3 Cards de resumo (topo)
- **Total do mês** — soma de todas as despesas do `month_ref`
- **Pago** — soma das com `status = pago`
- **Pendente** — soma das com `status = pendente`
- **% quitado** — anel de progresso (pago / total)

### 4.4 Tabela principal
Colunas, na mesma ordem da planilha original:
`Vencimento | Categoria | Descrição | Valor | Pagamento | Status | Observação`

- Cada linha tem uma stripe lateral colorida (verde = pago, âmbar = pendente)
  para leitura rápida por varredura visual, igual à planilha original
- Categoria como badge colorido (cor por categoria, não uma cor única)
- Observação com link clicável quando aplicável
- Botão de excluir aparece só no hover da linha

### 4.5 Edição inline
- Clique em qualquer célula (vencimento, descrição, valor, observação) abre
  edição direta, sem modal — Enter confirma, Esc cancela, blur confirma
- Clique no badge de status alterna Pago ⇄ Pendente
- Categoria editável via select inline

### 4.6 Criação
- Botão "+ Nova despesa" insere uma linha em branco já em modo de edição
  no topo da lista

### 4.7 Busca e filtros
- Campo de busca por descrição ou categoria
- Toggle "Só pendentes"

### 4.8 Sincronização em tempo real
- Supabase Realtime: mudanças feitas em outro dispositivo ou direto no
  banco refletem na tela automaticamente (`subscribeToExpenses`)

---

## 5. Sistema de design

### Tokens — tema escuro (`THEMES.dark`)
| Token | Hex | Uso |
|---|---|---|
| `pageBg` | gradiente radial `#131A30 → #0A0D18 → #08090F` | Fundo da página |
| `surface` | `#12162860` | Cards, tabela (com blur) |
| `border` / `borderSubtle` | `#232A45` / `#1B2138` | Bordas padrão / linhas da tabela |
| `textPrimary` | `#EDF0F7` | Texto principal |
| `textMuted` / `textFaint` | `#8891A8` / `#606A85` | Texto secundário |
| `accent` → `accentTo` | `#3FD6C4` → `#5B7FF5` | Marca, botão primário, foco |
| `success` / `successText` | `#3FD6C4` / `#5EE0C4` | Status pago |
| `warning` | `#F2B84B` | Status pendente |
| `danger` | `#F5738C` | Ação destrutiva (excluir) |

### Tokens — tema claro (`THEMES.light`)
| Token | Hex | Uso |
|---|---|---|
| `pageBg` | gradiente radial `#FFFFFF → #F4F6FB → #EAEDF6` | Fundo da página |
| `surface` | `#FFFFFFB3` | Cards, tabela (com blur) |
| `border` / `borderSubtle` | `#E1E5F0` / `#EAEDF5` | Bordas padrão / linhas da tabela |
| `textPrimary` | `#131826` | Texto principal |
| `textMuted` / `textFaint` | `#5B6478` / `#8890A3` | Texto secundário |
| `accent` → `accentTo` | `#0E9488` → `#3B5FE0` | Marca, botão primário, foco |
| `success` / `successText` | `#0D9488` | Status pago |
| `warning` | `#B45309` | Status pendente |
| `danger` | `#BE123C` | Ação destrutiva (excluir) |

### Categorias (variante por tema)
| Categoria | Escuro | Claro |
|---|---|---|
| Outros | `#94A3B8` | `#475569` |
| DAAE | `#5EA8F2` | `#1D4ED8` |
| CondInvest | `#B399F5` | `#7C3AED` |
| Imposto | `#F5738C` | `#BE123C` |
| Caixa | `#F2B84B` | `#B45309` |
| CPFL | `#3FD6C4` | `#0F766E` |

### Tipografia
- **Outfit** (500–700) — títulos, eyebrow, month label
- **Inter** — corpo, botões, inputs
- **JetBrains Mono** — valores em R$, datas, percentuais

### Elemento de assinatura
Anel de progresso (`ProgressRing`) representando `% quitado` do mês —
reforça a identidade de "dashboard financeiro" além da tabela. Cores do
gradiente do anel também trocam por tema (`ring1`/`ring2`).

### Padrões de interação
- Transições suaves (150–600ms) em hover, foco, mudança de valores e
  troca de tema
- Sem uso de `<form>` nativo — handlers `onClick` / `onChange`
- Sem `localStorage`/`sessionStorage` — estado do tema fica em memória
  (`useState`) no protótipo; em produção pode persistir em cookie/DB
  por usuário se necessário

---

## 6. Estrutura de arquivos (Next.js)

```
app/
  page.tsx                 → tela principal (monta GastosApp)
  layout.tsx
components/
  GastosApp.tsx             → componente principal (já entregue)
  ProgressRing.tsx
  ExpenseRow.tsx             → (opcional: extrair linha da tabela)
lib/
  supabaseClient.ts          → cliente + queries + realtime (já entregue)
  types.ts                   → Category, Expense, ExpenseStatus
  theme.ts                   → (opcional: mover objeto THEMES pra cá)
schema.sql                   → schema Supabase (já entregue)
.env.local
  NEXT_PUBLIC_SUPABASE_URL=
  NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

---

## 7. Roadmap sugerido

1. **v1** — protótipo com dados em memória, visual final definido
2. **v2 (atual)** — tema claro/escuro com toggle no header
3. **v3** — plugar `lib/supabaseClient.ts` no lugar do `useState`,
   criar projeto Next.js real, deploy na Vercel; persistir preferência
   de tema (ex: `localStorage` fora do ambiente de artifact, ou coluna
   `theme_preference` no perfil do usuário)
4. **v4** — gráfico de evolução mensal (usando `monthly_summary`),
   distribuição por categoria (pizza), export CSV/PDF do mês
5. **v5** — autenticação (Supabase Auth) se for multiusuário/família

---
