# PROMPT — Migração Completa do MAI Finance (FinFam) de Next.js para Python + Flet

> Cole este prompt no Antigravity como instrução inicial do agente. Ele foi escrito para ser autossuficiente (o agente não tem acesso a este chat, só ao repositório).

---

## 1. Contexto

Você vai migrar **100% do código** de um sistema de gestão financeira pessoal chamado **MAI Finance** (repositório `financas_martins`, nome interno `mai-finance`), que hoje é uma aplicação **Next.js 16 + React 19 + TypeScript + Supabase**, para uma aplicação **Python usando a biblioteca Flet**.

- **O banco de dados NÃO muda.** Continua sendo o mesmo projeto Supabase (Postgres), com o schema já existente (`schema.sql`). Não crie, remova nem altere tabelas, colunas, views, funções, triggers ou policies de RLS. A migração é só de camada de aplicação.
- O código-fonte atual está no repositório em `https://github.com/brunovdl/financas_martins.git`. Clone-o, leia todo o código (`app/`, `components/`, `lib/`, `context/`, `schema.sql`, `README.md`) antes de escrever qualquer linha nova, para garantir paridade total de comportamento.
- Trabalhe com **técnica de vibe coding incremental**: implemente por fases, rode/teste cada fase antes de avançar para a próxima, e só siga adiante quando a fase anterior estiver funcional. Não tente gerar o projeto inteiro em um único passo.

## 2. Stack de destino

- **Linguagem:** Python 3.11+
- **UI:** Flet (última versão estável)
- **Modo de execução alvo:** aplicação Flet rodando como **web app** (`flet run --web` / `ft.app(view=ft.WEB_BROWSER)`), para manter o mesmo modelo de uso do sistema atual (acesso via navegador, deploy em container). Se durante a implementação você identificar vantagem clara em also disponibilizar como app desktop (multi-plataforma do Flet), deixe isso como opção configurável, mas o alvo principal é web.
- **Banco de dados:** Supabase (Postgres) — mesmo projeto, mesmo schema. Use o cliente oficial `supabase-py` para as operações equivalentes às hoje feitas em `lib/supabaseClient.ts`.
- **Deploy:** Docker, no mesmo padrão do `Dockerfile` atual (multi-stage), publicado no EasyPanel. Gere um novo `Dockerfile` baseado em Python (ex.: `python:3.11-slim`), expondo a porta usada pelo Flet, com usuário não-root, seguindo o mesmo espírito de segurança do Dockerfile original.

## 3. Modelo de dados (referência — não alterar)

Tabelas existentes no Postgres (schema completo está em `schema.sql` no repo, leia-o integralmente):

- `mai_finance_users (id uuid, name, email, password_hash, created_at)` — RLS ativo.
- `categories (id uuid, name unique, color hex, created_at)` — RLS ativo.
- `expenses (id uuid, due_date date, category_id fk, description, amount numeric(12,2), payment_date date nullable, status enum('pago','pendente'), observation nullable, month_ref date, created_at, updated_at)` — RLS ativo, trigger `set_updated_at`.
- `backups (id uuid, type 'automatico'|'manual', categories_count, expenses_count, total_amount, data jsonb, created_at)` — RLS ativo.
- View `monthly_summary` (agregado por `month_ref`: total, total pendente, qtd pendente).
- Função `create_backup(backup_type)` já existe no banco (gera snapshot JSONB e mantém retenção de 3). Já é agendada via `pg_cron` quinzenalmente — **isso já roda no banco e não precisa ser recriado em Python**, apenas seja chamado quando o usuário pedir backup manual.

## 4. Funcionalidades a replicar (paridade total)

Leia o código-fonte de cada item abaixo antes de reescrever, para não perder regra de negócio nenhuma:

### 4.1 Autenticação (`lib/auth.ts`, `context/AuthContext.tsx`, `components/AuthPage.tsx`, `app/api/auth/*`)
- Hash de senha com **PBKDF2 + salt aleatório de 16 bytes, 1000 iterações, SHA-512**, formato armazenado `salt:hash` em hex. **Reimplemente exatamente esse algoritmo em Python** (`hashlib.pbkdf2_hmac`), pois os usuários já cadastrados no banco têm hashes nesse formato — se o algoritmo não for idêntico, ninguém consegue mais logar.
- Sessão via **JWT HS256 caseiro** (não usa biblioteca de JWT, é assinatura manual com HMAC) com expiração de 24h (`SESSION_DURATION_SECONDS = 86400`). Pode reimplementar manualmente igual ao original ou usar uma lib Python de JWT (ex. `PyJWT`) desde que o comportamento de expiração de 24h e os campos do payload (`userId`, `name`, `email`, `iat`, `exp`) sejam mantidos. Como a aplicação Flet não usa cookies de navegador da mesma forma que Next.js, adapte o armazenamento de sessão para o mecanismo de client storage do Flet (`page.client_storage`) ou storage de sessão do servidor, mantendo a expiração de 24h e logout automático ao expirar.
- Validação de senha mínima de 8 caracteres no cadastro e login.
- Tela de login/cadastro deve ter paridade visual e de fluxo com `AuthPage.tsx`.

### 4.2 Dashboard principal / gestão de despesas (`components/GastosApp.tsx` — arquivo maior, leia com atenção)
- Listagem de despesas filtradas por **mês de referência** (`month_ref`), com navegação entre meses.
- Cards/resumo do mês: total de despesas, total pendente, quantidade de pendências (usar a view `monthly_summary` ou replicar a mesma agregação).
- Anel de progresso (`ProgressRing.tsx`) mostrando proporção pago vs. pendente — reimplemente como componente visual equivalente no Flet (ex. `ft.ProgressRing` ou um customizado).
- CRUD completo de despesas: criar, editar, marcar como pago/pendente, excluir, com campos `due_date`, `category_id`, `description`, `amount`, `payment_date`, `status`, `observation`.
- Atualização em tempo real via Supabase Realtime (`subscribeToExpenses` em `lib/supabaseClient.ts`) — verifique se `supabase-py` suporta realtime/subscriptions no seu modo de uso; se a versão usada não suportar bem realtime em Python, implemente um polling leve como fallback e documente essa decisão no README do novo projeto.

### 4.3 Categorias (`components/CategoriesModal.tsx`)
- CRUD de categorias com nome único e cor em hex.
- Ao excluir categoria, as despesas vinculadas devem ficar sem categoria (`unlinkExpensesFromCategory`), nunca serem apagadas.

### 4.4 Clonagem de mês (`components/CloneMonthModal.tsx`)
- Duplicar despesas recorrentes de um mês para outro, com ajuste inteligente de datas (`due_date` recalculada para o novo `month_ref`, `status` resetado para `pendente`).

### 4.5 Importação em lote (`components/ImportModal.tsx`)
- Importação de despesas via arquivo estruturado (verifique o formato aceito no código atual — CSV/JSON/planilha) usando `bulkInsertExpenses`.

### 4.6 Backups (`components/BackupModal.tsx`)
- Listar backups existentes (tabela `backups`).
- Disparar backup manual chamando a função `create_backup('manual')` do Postgres via RPC do Supabase.
- Restaurar um backup (`restoreBackup`), repovoando categorias e despesas a partir do snapshot JSONB.

### 4.7 Assistente de IA / Chat (`components/ChatWidget.tsx`, `app/api/chat/route.ts`, `lib/chatCache.ts`)
- Widget de chat que usa a **API da Groq** (modelo `llama-3.3-70b-versatile`) para dar insights sobre os gastos do usuário.
- Reimplemente a chamada usando o **SDK Python oficial da Groq** (`groq` no PyPI), preservando o mesmo prompt/contexto enviado hoje (leia `app/api/chat/route.ts` para extrair o system prompt e a lógica de montagem de contexto financeiro).
- Replique a lógica de cache de respostas (`lib/chatCache.ts`) para evitar chamadas repetidas desnecessárias.

### 4.8 Integração Open Finance / cata-centavo (`lib/cataCentavo.ts`) — **atenção especial**
- Hoje essa integração usa o pacote Node `cata-centavo` como servidor **MCP (Model Context Protocol)**, conectado via stdio, para trazer dados da Pluggy (Open Finance).
- **Esse pacote é Node-only e não existe equivalente Python direto.** Você tem duas opções — escolha a que for viável e documente a decisão:
  1. **Preferencial:** Reimplementar a integração chamando **diretamente a API REST da Pluggy** a partir do Python (autenticação com `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET`, obtenção de `item_id`(s) via `PLUGGY_ITEM_IDS`/`PLUGGY_ITEM_ID_*`, e consumo dos endpoints de transações/contas necessários), sem depender do MCP.
  2. **Alternativa (fallback):** manter um pequeno microsserviço Node.js isolado (só com o `cata-centavo`) rodando como sidecar no mesmo container/stack, exposto via HTTP simples, e o Python consome esse HTTP internamente. Use isso apenas se a opção 1 não for viável no tempo disponível.
- Preserve as mesmas variáveis de ambiente (`PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`, `PLUGGY_ITEM_IDS`/`PLUGGY_ITEM_ID_*`) e o comportamento de fallback de diretórios de cache/dados.

### 4.9 Design / tema (`lib/theme.ts`, `app/globals.css`)
- Replique o **dark mode financeiro elegante** como tema principal (com opção de tema claro, já que o código atual tem tokens `dark` e `light`).
- Reaproveite a paleta de cores exata definida em `THEMES` e `CATEGORIES` (cores hex) para manter a identidade visual.
- Ícones: o projeto atual usa `lucide-react`; no Flet, use os ícones nativos (`ft.icons`) escolhendo os mais próximos visualmente, ou uma lib de ícones compatível com Flet.

## 5. Regras técnicas e de processo

1. **Não altere o schema do banco.** Qualquer necessidade de nova coluna/tabela deve ser discutida antes, não implementada silenciosamente.
2. **Não reescreva as políticas de RLS nem a função `create_backup`/o agendamento `pg_cron`** — eles já existem no Postgres e continuam servindo à nova aplicação Python.
3. Estruture o novo projeto Python de forma modular, por exemplo:
   ```
   mai_finance_flet/
     app.py                 # entrypoint Flet
     config.py               # variáveis de ambiente
     db/
       supabase_client.py    # equivalente ao lib/supabaseClient.ts
       auth.py                # equivalente ao lib/auth.ts
     services/
       expenses.py
       categories.py
       backups.py
       chat.py                # integração Groq
       open_finance.py        # integração Pluggy/cata-centavo
     ui/
       auth_view.py
       dashboard_view.py
       categories_modal.py
       clone_month_modal.py
       import_modal.py
       backup_modal.py
       chat_widget.py
       theme.py
     tests/
     Dockerfile
     requirements.txt
     README.md
   ```
4. Use variáveis de ambiente equivalentes às atuais (`NEXT_PUBLIC_SUPABASE_URL` → `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` → `SUPABASE_ANON_KEY`, `GROQ_API_KEY`, `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`, `PLUGGY_ITEM_IDS`, `JWT_SECRET`), documentando todas em um `.env.example`.
5. Escreva testes básicos para as regras críticas: hashing/verificação de senha (garantindo compatibilidade com hashes já salvos no banco), cálculo de resumo mensal, clonagem de mês, e lógica de retenção/restauração de backup.
6. Ao final, escreva um `README.md` novo explicando como rodar localmente (`flet run`), como buildar a imagem Docker e quais decisões de migração foram tomadas (principalmente sobre o item 4.8).

## 6. Plano de execução por fases (siga nesta ordem, testando cada uma)

1. **Fase 0 — Setup:** clonar o repo original, mapear todo o código, criar o novo projeto Python/Flet vazio com estrutura de pastas, configurar `supabase-py` e validar conexão com o banco existente (leitura simples de `categories`).
2. **Fase 1 — Autenticação:** implementar hashing PBKDF2 compatível, login/cadastro, sessão de 24h. Testar login com um usuário já existente no banco.
3. **Fase 2 — Categorias:** CRUD completo + tema/cores.
4. **Fase 3 — Despesas + Dashboard:** CRUD de despesas, filtro por mês, cards de resumo, anel de progresso.
5. **Fase 4 — Clonagem de mês e Importação em lote.**
6. **Fase 5 — Backups:** listar, criar (RPC `create_backup`), restaurar.
7. **Fase 6 — Chat com IA (Groq).**
8. **Fase 7 — Integração Open Finance (Pluggy/cata-centavo).**
9. **Fase 8 — Empacotamento:** Dockerfile Python, variáveis de ambiente, ajustes finais de UI/tema, README.

Ao final de cada fase, rode a aplicação e confirme visualmente/funcionalmente que o comportamento é equivalente ao sistema Next.js original antes de avançar.

## 7. Critério de aceite final

- Login funciona com os usuários já existentes no banco (sem precisar recriar senhas).
- Todas as telas/fluxos do sistema atual têm equivalente funcional em Flet.
- Nenhuma alteração foi feita no schema, RLS, funções ou triggers do Postgres.
- A aplicação builda em Docker e sobe como app web Flet.
- Documentação clara sobre a decisão tomada para a integração Pluggy/cata-centavo.