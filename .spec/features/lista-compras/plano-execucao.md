# Plano de execução — lista-compras

> gerado por `onp-spec plano` em 2026-09-20 14:44 — NÃO edite à mão;
> mudou tasks.md ou a config? Regenere: `onp-spec plano lista-compras --sequencial`

## Resumo — o que vai acontecer

- **modo SEQUENCIAL (escolha do usuário)**: 7 tarefa(s) pendente(s), UMA APÓS A OUTRA, na árvore principal
- sem worktrees e sem paralelismo — cada tarefa roda numa janela de contexto limpa, na ordem do tasks.md
- tudo acontece na branch de trabalho `spec/lista-compras`; levar para a main é decisão sua

## Ordem de execução (uma tarefa após a outra)

| tarefa | título | modelo | esforço |
|---|---|---|---|
| T-015 | Modelagem das tabelas no Supabase (shopping_items, shopping_history, shopping_frequent_items) com RLS | `claude-sonnet-5` | medium |
| T-016 | Serviço de gerenciamento de itens, atalhos rápidos e cache offline | `claude-sonnet-5` | medium |
| T-017 | Módulo de geolocalização e cotação inteligente com Groq + Busca Web | `claude-sonnet-5` | high |
| T-018 | Sincronização em tempo real via Supabase Realtime | `claude-sonnet-5` | medium |
| T-019 | Interface da Lista de Compras: cadastro, corredores e cotação | `claude-sonnet-5` | high |
| T-020 | Interface do Modo Mercado, métricas de carrinho e finalização com despesa | `claude-sonnet-5` | high |
| T-021 | Visibilidade no Dashboard (card de pendências) e barra de navegação | `claude-sonnet-5` | medium |

## Gestão de branches e commits

1. branch de trabalho `spec/lista-compras` criada do ponto atual (se ainda não existir)
2. as tarefas rodam nela mesma, na ordem — **1 tarefa = 1 commit** (`T-xxx feature: título`), marcada `[concluida]` só com trabalho feito
3. gate final na branch de trabalho: `onp-spec verify lista-compras` + `onp-spec audit --ci` — **exit 0 ou não está pronto**

## Como executar

### ▶ Sequencial no Antigravity (uma tarefa após a outra, sem Claude CLI)

1. **Entre na branch de trabalho** (terminal, na raiz do repositório):

```bash
git checkout -b spec/lista-compras   # ou: git checkout spec/lista-compras
```

2. **Execute as tarefas NA ORDEM, uma após a outra** (janela limpa por tarefa
   ajuda o foco; a próxima só começa quando a anterior commitou):

#### Prompt — T-015

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-015 — "Modelagem das tabelas no Supabase (shopping_items, shopping_history, shopping_frequent_items) com RLS"
  critérios/refs: AC-021 (Adição de item com quantidade, unidade e corredor), AC-029 (Conversão da compra em despesa no MAI Finance e arquivamento)
  arquivos permitidos (e seus testes): schema.sql, mai_finance_flet/db/shopping.py, mai_finance_flet/tests/test_shopping_db.py
  mensagem de commit: "T-015 lista-compras: Modelagem das tabelas no Supabase (shopping_items, shopping_history, shopping_frequent_items) com RLS"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-015 concluida` após o commit.

#### Prompt — T-016

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-016 — "Serviço de gerenciamento de itens, atalhos rápidos e cache offline"
  critérios/refs: AC-021 (Adição de item com quantidade, unidade e corredor), AC-022 (Sugestões e atalhos rápidos de itens frequentes), AC-028 (Resiliência offline com sincronização automática)
  arquivos permitidos (e seus testes): mai_finance_flet/services/shopping_service.py, mai_finance_flet/tests/test_shopping_service.py
  mensagem de commit: "T-016 lista-compras: Serviço de gerenciamento de itens, atalhos rápidos e cache offline"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-016 concluida` após o commit.

#### Prompt — T-017

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-017 — "Módulo de geolocalização e cotação inteligente com Groq + Busca Web"
  critérios/refs: AC-023 (Detecção de localização para consulta de mercados da região), AC-024 (Cotação comparativa e seleção de mercado único para a compra), AC-025 (Priorização de melhor custo-benefício em marcas conhecidas)
  arquivos permitidos (e seus testes): mai_finance_flet/services/market_ai_service.py, mai_finance_flet/services/geo_service.py, mai_finance_flet/tests/test_market_ai.py
  mensagem de commit: "T-017 lista-compras: Módulo de geolocalização e cotação inteligente com Groq + Busca Web"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-017 concluida` após o commit.

#### Prompt — T-018

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-018 — "Sincronização em tempo real via Supabase Realtime"
  critérios/refs: AC-027 (Sincronização em tempo real entre celulares via Supabase Realtime)
  arquivos permitidos (e seus testes): mai_finance_flet/services/shopping_realtime.py, mai_finance_flet/tests/test_shopping_realtime.py
  mensagem de commit: "T-018 lista-compras: Sincronização em tempo real via Supabase Realtime"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-018 concluida` após o commit.

#### Prompt — T-019

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-019 — "Interface da Lista de Compras: cadastro, corredores e cotação"
  critérios/refs: AC-021 (Adição de item com quantidade, unidade e corredor), AC-022 (Sugestões e atalhos rápidos de itens frequentes), AC-024 (Cotação comparativa e seleção de mercado único para a compra), AC-025 (Priorização de melhor custo-benefício em marcas conhecidas)
  arquivos permitidos (e seus testes): mai_finance_flet/ui/shopping_view.py, mai_finance_flet/ui/components/shopping_item_card.py, mai_finance_flet/ui/components/market_quote_modal.py, mai_finance_flet/tests/test_shopping_view.py
  mensagem de commit: "T-019 lista-compras: Interface da Lista de Compras: cadastro, corredores e cotação"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-019 concluida` após o commit.

#### Prompt — T-020

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-020 — "Interface do Modo Mercado, métricas de carrinho e finalização com despesa"
  critérios/refs: AC-026 (Interface do Modo Mercado por corredores e métricas de carrinho), AC-029 (Conversão da compra em despesa no MAI Finance e arquivamento)
  arquivos permitidos (e seus testes): mai_finance_flet/ui/shopping_market_mode.py, mai_finance_flet/ui/components/shopping_finish_modal.py, mai_finance_flet/tests/test_shopping_market_mode.py
  mensagem de commit: "T-020 lista-compras: Interface do Modo Mercado, métricas de carrinho e finalização com despesa"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-020 concluida` após o commit.

#### Prompt — T-021

```
Você executa UMA tarefa da feature "lista-compras" (fluxo onp-spec, spec-anchored).
Leia primeiro: .spec/features/lista-compras/spec.md, .spec/features/lista-compras/tasks.md e .spec/constituicao.md.

Sua tarefa (somente ela):
T-021 — "Visibilidade no Dashboard (card de pendências) e barra de navegação"
  critérios/refs: AC-030 (Card de compras no Dashboard e destino na barra de navegação)
  arquivos permitidos (e seus testes): mai_finance_flet/ui/dashboard_view.py, mai_finance_flet/ui/nav.py, mai_finance_flet/app.py, mai_finance_flet/tests/test_shopping_nav.py
  mensagem de commit: "T-021 lista-compras: Visibilidade no Dashboard (card de pendências) e barra de navegação"

Regras inegociáveis:
- Todo critério de aceite referenciado vira teste com @spec:AC-xxx no título.
- NUNCA enfraqueça, pule (skip/todo) ou apague um teste para passar — teste pulado não é prova e o audit acusa.
- Rode os testes localmente com `.venv\Scripts\python.exe -m pytest mai_finance_flet/tests/ -v` até passarem.
- NÃO edite tasks.md, NÃO rode onp-spec verify/audit e NÃO toque em outras tarefas — o orquestrador cuida disso.
- Ao final de CADA tarefa: `git add` só no que você tocou e um commit próprio.
```

`node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs tarefa lista-compras T-021 concluida` após o commit.

3. **Gate final** (exit 0 ou não está pronto):

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs verify lista-compras
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs audit --ci
```

4. **Acompanhamento (a cada ~1 min, enquanto executa)**: avise ANTES de começar
   que o trabalho roda em background e que o resumo completo vem ao final. Marque
   cada tarefa no ledger ao começar e ao terminar (é disso que a tabela é feita):

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs evento --run financas_martins-lista-compras-mu9xgm6f --tipo tarefa --tarefa <T-xxx> --faixa seq --estado executando   # ao começar
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs evento --run financas_martins-lista-compras-mu9xgm6f --tipo tarefa --tarefa <T-xxx> --faixa seq --estado concluida    # após o commit
```

   E a cada ~1 min poste no chat a TABELA de andamento + um parágrafo curto,
   registrando o texto no ledger:

```bash
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs resumo lista-compras --tabela   # a tabela — cole no chat
node .agents/skills/onp-spec-driven/scripts/onp-spec.mjs resumo lista-compras --gravar --origem ia --texto "<2 a 4 frases do que está rolando>"
```

