# Tasks: Migração MAI Finance — Next.js → Python/Flet

> feature: migracao-flet

## T-001 — Setup do projeto Python/Flet e validação de conexão [concluida]
- Refs: US-009, AC-019, AC-020
- Arquivos: mai_finance_flet/app.py, mai_finance_flet/config.py, mai_finance_flet/requirements.txt, mai_finance_flet/.env.example
- Esforço: baixo
- Notas: Criar estrutura de pastas, requirements.txt (flet, supabase, python-dotenv, pyjwt, groq, openpyxl, httpx), config.py para vars de ambiente, .env.example, app.py esqueleto ft.app e validar leitura simples de categories no Supabase.

## T-002 — Módulo de autenticação (PBKDF2 + JWT) [concluida]
- Refs: AC-001, AC-002, AC-003, AC-004
- Arquivos: mai_finance_flet/db/auth.py, mai_finance_flet/tests/test_auth.py
- Esforço: medio
- Notas: verify_password com PBKDF2-HMAC-SHA512, 1000 iterações, salt 16 bytes, formato salt_hex:hash_hex. hash_password para cadastro. create_token/verify_token com PyJWT HS256, expiração 24h, campos userId/name/email/iat/exp.

## T-003 — Módulo supabase_client.py com suporte a RLS [concluida]
- Refs: US-001, US-002, US-003, US-006
- Arquivos: mai_finance_flet/db/supabase_client.py
- Esforço: baixo
- Notas: Cliente Supabase singleton com **Anon Key** (igual ao Next.js atual, sem Supabase Auth nativo). Validar conexão com leitura de categories. Polling helper de 30s para atualização reativa de listas.

## T-004 — Tela de autenticação (login e cadastro) [concluida]
- Refs: AC-001, AC-004
- Arquivos: mai_finance_flet/ui/auth_view.py, mai_finance_flet/tests/test_auth_view.py
- Esforço: medio
- Notas: Campos e-mail, senha, nome. Validação inline. Feedback visual de erro. Token armazenado em page.client_storage. Redirecionamento ao expirar. Paridade visual com AuthPage.tsx.

## T-005 — Serviço de despesas e view do dashboard [concluida]
- Refs: AC-005, AC-006, AC-007, AC-008, AC-009
- Arquivos: mai_finance_flet/services/expenses.py, mai_finance_flet/ui/dashboard_view.py, mai_finance_flet/ui/components/progress_ring.py, mai_finance_flet/tests/test_expenses.py
- Esforço: alto
- Notas: list_expenses(month_ref), create/update/delete_expense, toggle_status (preenche payment_date ao marcar pago). Dashboard: navegação mensal, cards via monthly_summary, ProgressRing. Polling 30s como fallback para Realtime.

## T-006 — Serviço e modal de categorias [concluida]
- Refs: AC-010, AC-011
- Arquivos: mai_finance_flet/services/categories.py, mai_finance_flet/ui/categories_modal.py, mai_finance_flet/tests/test_categories.py
- Esforço: medio
- Notas: list/create/update/delete_category. **Verificar no Supabase (via supabase-mcp ou consulta direta) se as colunas `type` e `icon` existem no banco real antes de inserir** — se não existirem, omití-las. Usar coluna `color` (conforme schema.sql, não `color_hex`). delete_category desvincula expenses (SET category_id=NULL) antes de deletar. Modal com picker de cor hex, formulário inline, confirmação de exclusão.

## T-007 — Modal de clonagem de mês [concluida]
- Refs: AC-012
- Arquivos: mai_finance_flet/services/clone_month.py, mai_finance_flet/ui/clone_month_modal.py, mai_finance_flet/tests/test_clone_month.py
- Esforço: medio
- Notas: clone_month(source, target): ajusta due_date para mesmo dia no mês destino (último dia do mês quando dia inexistente), reseta status=pendente, payment_date=NULL, month_ref=target. Testes de paridade de datas (ex.: 31 jan → fev).

## T-008 — Modal de importação em lote CSV/XLS/XLSX [concluida]
- Refs: AC-013
- Arquivos: mai_finance_flet/services/import_expenses.py, mai_finance_flet/ui/import_modal.py
- Esforço: medio
- Notas: Parser CSV (stdlib csv), XLS/XLSX (openpyxl). Validação de colunas obrigatórias. bulk_insert(rows). ft.FilePicker para upload. Preview das linhas, relatório de inválidas, confirmação antes de inserir.

## T-009 — Serviço e modal de backups [concluida]
- Refs: AC-014, AC-015
- Arquivos: mai_finance_flet/services/backups.py, mai_finance_flet/ui/backup_modal.py, mai_finance_flet/tests/test_backups.py
- Esforço: medio
- Notas: list_backups(), create_manual_backup() via RPC create_backup('manual'), restore_backup(id) que apaga e repopula categories e expenses do JSONB. Modal com lista, botões criar/restaurar e diálogo de confirmação.

## T-010 — Assistente de IA Groq com cache [concluida]
- Refs: AC-016, AC-017
- Arquivos: mai_finance_flet/services/chat.py, mai_finance_flet/ui/chat_widget.py
- Esforço: medio
- Notas: SDK groq com llama-3.3-70b-versatile. Cache em memória (dict hash_pergunta→resposta) com TTL 1h. Contexto financeiro: despesas e resumo do mês atual. Widget: histórico, input, ProgressRing de digitação, confirmação antes de ações destrutivas.


## T-012 — Tema visual dark/light e navegação principal [concluida]
- Refs: US-009
- Arquivos: mai_finance_flet/ui/theme.py, mai_finance_flet/ui/nav.py
- Esforço: baixo
- Notas: Paleta dark (surface #151B2E, accent #3FD6C4, muted #94A3B8, warning #F2B84B, success #10B981, error #F5738C) e light (#F0F4FA). ft.NavigationBar com 4 abas. Toggle de tema em page.client_storage.

## T-013 — Dockerfile Python e documentação final [concluida]
- Refs: AC-019, AC-020
- Arquivos: mai_finance_flet/Dockerfile, mai_finance_flet/README.md
- Esforço: baixo
- Notas: Dockerfile multi-stage python:3.11-slim, usuário não-root, porta 8550. README com como rodar localmente, como buildar Docker, decisões de migração (Pluggy opção 1, Realtime polling 30s).
