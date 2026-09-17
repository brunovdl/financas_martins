# Plano de execução — migracao-flet

> gerado por `onp-spec plano` em 2026-09-15 03:27 — NÃO edite à mão;
> mudou tasks.md ou a config? Regenere: `onp-spec plano migracao-flet --sequencial`

## Resumo — o que vai acontecer

- **modo SEQUENCIAL (escolha do usuário)**: 12 tarefa(s) pendente(s), UMA APÓS A OUTRA, na árvore principal
- sem worktrees e sem paralelismo — cada tarefa roda numa janela de contexto limpa, na ordem do tasks.md
- tudo acontece na branch de trabalho `spec/migracao-flet`; levar para a main é decisão sua

## Ordem de execução (uma tarefa após a outra)

| tarefa | título | modelo | esforço |
|---|---|---|---|
| T-001 | Setup do projeto Python/Flet e validação de conexão | `claude-sonnet-5` | low |
| T-002 | Módulo de autenticação (PBKDF2 + JWT) | `claude-sonnet-5` | medium |
| T-003 | Módulo supabase_client.py com suporte a RLS | `claude-sonnet-5` | low |
| T-004 | Tela de autenticação (login e cadastro) | `claude-sonnet-5` | medium |
| T-005 | Serviço de despesas e view do dashboard | `claude-sonnet-5` | high |
| T-006 | Serviço e modal de categorias | `claude-sonnet-5` | medium |
| T-007 | Modal de clonagem de mês | `claude-sonnet-5` | medium |
| T-008 | Modal de importação em lote CSV/XLS/XLSX | `claude-sonnet-5` | medium |
| T-009 | Serviço e modal de backups | `claude-sonnet-5` | medium |
| T-010 | Assistente de IA Groq com cache | `claude-sonnet-5` | medium |
| T-012 | Tema visual dark/light e navegação principal | `claude-sonnet-5` | low |
| T-013 | Dockerfile Python e documentação final | `claude-sonnet-5` | low |

## Gestão de branches e commits

1. branch de trabalho `spec/migracao-flet` criada do ponto atual (se ainda não existir)
2. as tarefas rodam nela mesma, na ordem — **1 tarefa = 1 commit** (`T-xxx feature: título`), marcada `[concluida]` só com trabalho feito
3. gate final na branch de trabalho: `onp-spec verify migracao-flet` + `onp-spec audit --ci` — **exit 0 ou não está pronto**

## Como executar

### ▶ Sequencial no Antigravity (uma tarefa após a outra, sem Claude CLI)

1. **Entre na branch de trabalho** (terminal, na raiz do repositório):

```bash
git checkout -b spec/migracao-flet   # ou: git checkout spec/migracao-flet
```

2. **Execute as tarefas NA ORDEM, uma após a outra** (janela limpa por tarefa
   ajuda o foco; a próxima só começa quando a anterior commitou):

#### Prompt — T-001

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-001 — "Setup do projeto Python/Flet e validação de conexão"
  critérios/refs: AC-019 (Dockerfile Python multi-stage com usuário não-root), AC-020 (Variáveis de ambiente documentadas em .env.example)
  arquivos permitidos (e seus testes): mai_finance_flet/app.py, mai_finance_flet/config.py, mai_finance_flet/requirements.txt, mai_finance_flet/.env.example
  mensagem de commit: "T-001 migracao-flet: Setup do projeto Python/Flet e validação de conexão"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-001 concluida` após o commit.

#### Prompt — T-002

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-002 — "Módulo de autenticação (PBKDF2 + JWT)"
  critérios/refs: AC-001 ([título do critério de aceite]), AC-002 (Função verify_password compatível com hashes legados), AC-003 (Sessão expira após 24h e redireciona para login), AC-004 (Senha mínima de 8 caracteres no cadastro)
  arquivos permitidos (e seus testes): mai_finance_flet/db/auth.py, mai_finance_flet/tests/test_auth.py
  mensagem de commit: "T-002 migracao-flet: Módulo de autenticação (PBKDF2 + JWT)"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-002 concluida` após o commit.

#### Prompt — T-003

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-003 — "Módulo supabase_client.py com suporte a RLS"
  critérios/refs: US-001, US-002, US-003, US-006
  arquivos permitidos (e seus testes): mai_finance_flet/db/supabase_client.py
  mensagem de commit: "T-003 migracao-flet: Módulo supabase_client.py com suporte a RLS"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-003 concluida` após o commit.

#### Prompt — T-004

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-004 — "Tela de autenticação (login e cadastro)"
  critérios/refs: AC-001 ([título do critério de aceite]), AC-004 (Senha mínima de 8 caracteres no cadastro)
  arquivos permitidos (e seus testes): mai_finance_flet/ui/auth_view.py, mai_finance_flet/tests/test_auth_view.py
  mensagem de commit: "T-004 migracao-flet: Tela de autenticação (login e cadastro)"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-004 concluida` após o commit.

#### Prompt — T-005

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-005 — "Serviço de despesas e view do dashboard"
  critérios/refs: AC-005 (Listagem filtrada por month_ref), AC-006 (Cards de resumo usando a view monthly_summary), AC-007 (ProgressRing proporcional ao status), AC-008 (CRUD completo de despesas), AC-009 (Marcar despesa como paga preenche payment_date)
  arquivos permitidos (e seus testes): mai_finance_flet/services/expenses.py, mai_finance_flet/ui/dashboard_view.py, mai_finance_flet/ui/components/progress_ring.py, mai_finance_flet/tests/test_expenses.py
  mensagem de commit: "T-005 migracao-flet: Serviço de despesas e view do dashboard"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-005 concluida` após o commit.

#### Prompt — T-006

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-006 — "Serviço e modal de categorias"
  critérios/refs: AC-010 (Nome de categoria deve ser único), AC-011 (Exclusão de categoria desvincula despesas sem apagá-las)
  arquivos permitidos (e seus testes): mai_finance_flet/services/categories.py, mai_finance_flet/ui/categories_modal.py, mai_finance_flet/tests/test_categories.py
  mensagem de commit: "T-006 migracao-flet: Serviço e modal de categorias"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-006 concluida` após o commit.

#### Prompt — T-007

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-007 — "Modal de clonagem de mês"
  critérios/refs: AC-012 (Clonagem ajusta due_date e reseta status)
  arquivos permitidos (e seus testes): mai_finance_flet/services/clone_month.py, mai_finance_flet/ui/clone_month_modal.py, mai_finance_flet/tests/test_clone_month.py
  mensagem de commit: "T-007 migracao-flet: Modal de clonagem de mês"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-007 concluida` após o commit.

#### Prompt — T-008

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-008 — "Modal de importação em lote CSV/XLS/XLSX"
  critérios/refs: AC-013 (Upload e inserção bulk via arquivo estruturado)
  arquivos permitidos (e seus testes): mai_finance_flet/services/import_expenses.py, mai_finance_flet/ui/import_modal.py
  mensagem de commit: "T-008 migracao-flet: Modal de importação em lote CSV/XLS/XLSX"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-008 concluida` após o commit.

#### Prompt — T-009

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-009 — "Serviço e modal de backups"
  critérios/refs: AC-014 (Criação de backup manual via RPC do Supabase), AC-015 (Restauração repovoa categorias e despesas do snapshot)
  arquivos permitidos (e seus testes): mai_finance_flet/services/backups.py, mai_finance_flet/ui/backup_modal.py, mai_finance_flet/tests/test_backups.py
  mensagem de commit: "T-009 migracao-flet: Serviço e modal de backups"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-009 concluida` após o commit.

#### Prompt — T-010

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-010 — "Assistente de IA Groq com cache"
  critérios/refs: AC-016 (Chat responde usando contexto financeiro do usuário), AC-017 (Cache evita chamadas repetidas à API Groq)
  arquivos permitidos (e seus testes): mai_finance_flet/services/chat.py, mai_finance_flet/ui/chat_widget.py
  mensagem de commit: "T-010 migracao-flet: Assistente de IA Groq com cache"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-010 concluida` após o commit.

#### Prompt — T-012

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-012 — "Tema visual dark/light e navegação principal"
  critérios/refs: US-009
  arquivos permitidos (e seus testes): mai_finance_flet/ui/theme.py, mai_finance_flet/ui/nav.py
  mensagem de commit: "T-012 migracao-flet: Tema visual dark/light e navegação principal"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-012 concluida` após o commit.

#### Prompt — T-013

```
Você executa UMA tarefa da feature "migracao-flet" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/migracao-flet/spec.md, .spec/features/migracao-flet/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-013 — "Dockerfile Python e documentação final"
  critérios/refs: AC-019 (Dockerfile Python multi-stage com usuário não-root), AC-020 (Variáveis de ambiente documentadas em .env.example)
  arquivos permitidos (e seus testes): mai_finance_flet/Dockerfile, mai_finance_flet/README.md
  mensagem de commit: "T-013 migracao-flet: Dockerfile Python e documentação final"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `../.venv/Scripts/python.exe -m pytest mai_finance_flet/tests/ android/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa migracao-flet T-013 concluida` após o commit.

3. **Gate final** (exit 0 ou não está pronto):

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs verify migracao-flet
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs audit --ci
```

4. **Acompanhamento (a cada ~1 min, enquanto executa)**: avise ANTES de começar
   que o trabalho roda em background e que o resumo completo vem ao final. Marque
   cada tarefa no ledger ao começar e ao terminar (é disso que a tabela é feita):

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs evento --run financas_martins-migracao-flet-mu2433pn --tipo tarefa --tarefa <T-xxx> --faixa seq --estado executando   # ao começar
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs evento --run financas_martins-migracao-flet-mu2433pn --tipo tarefa --tarefa <T-xxx> --faixa seq --estado concluida    # após o commit
```

   E a cada ~1 min poste no chat a TABELA de andamento + um parágrafo curto,
   registrando o texto no ledger:

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs resumo migracao-flet --tabela   # a tabela — cole no chat
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs resumo migracao-flet --gravar --origem ia --texto "<2 a 4 frases do que está rolando>"
```

