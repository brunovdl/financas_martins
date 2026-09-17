# MAI Finance — Versão Python + Flet Web App

Aplicação web moderna de gestão financeira pessoal para Bruno e sua esposa, migrada com 100% de paridade de regras de negócio e persistência a partir do Next.js original, mantendo o banco de dados Supabase (Postgres) inalterado.

---

## 1. Visão Geral da Arquitetura

- **Linguagem & Framework de UI:** Python 3.11+ com Flet (`ft.app(view=ft.AppView.WEB_BROWSER)`).
- **Banco de Dados & Backend:** Supabase (PostgreSQL) com RLS ativado via `supabase-py`.
- **Autenticação:** Compatibilidade total com senhas existentes usando PBKDF2-HMAC-SHA512 (1000 iterações, salt de 16 bytes em hex) e tokens JWT HS256 com validade de 24 horas.
- **Resumo e Agregações:** Utiliza a view nativa `monthly_summary`, cards ampliados de métricas financeiras e fallback local.
- **Design System & Responsividade:** Dark Mode com fundo `#08090F` / `#151B2E`, Light Mode completo com atualização reativa integral, destaques em Teal `#3FD6C4` e layout adaptativo (Cards no mobile <768px e Tabela completa no desktop).
- **Alerta de Mês Anterior:** Ícone com badge contador e diálogo dedicado para consulta rápida de despesas pendentes do mês anterior.
- **Containerização:** Docker multi-stage com usuário não-root (`appuser`), porta padrão `8550`.

---

## 2. Decisões Técnicas e Histórico de Refatoração

1. **Compatibilidade de Senhas:** Reimplementação exata do algoritmo PBKDF2 do Node.js (`hashlib.pbkdf2_hmac`) para garantir que os usuários já cadastrados no Supabase façam login sem precisar redefinir credenciais.
2. **Atualização em Tempo Real vs. Polling:** Em substituição às subscriptions realtime do client TypeScript (que possuem limitações no wrapper Python do Supabase em certos ambientes web), foi implementado um polling leve e assíncrono de 30 segundos no `DashboardView` para manter a sincronização com o banco.
3. **Escopo Limpo de Produção:** Remoção completa dos módulos não necessários nesta versão (Importação de planilhas e Chat IA), mantendo a base de código 100% limpa, leve e segura.
4. **Arquitetura de Diálogos Flet 1.0:** Todos os modais ("Nova Despesa", "Categorias", "Clonar Mês", "Backups" e "Pendências Anteriores") migrados para a API moderna `page.show_dialog()` e `page.pop_dialog()`.
5. **Armazenamento de Sessão:** Abstração de persistência em `storage_util.py`, garantindo compatibilidade entre `shared_preferences`, `session` e `client_storage` do Flet.
6. **Categorias no Banco:** Uso estrito da coluna `color` (hex) conforme definido em `schema.sql`, omitindo colunas legadas como `type` e `icon`.

---

## 3. Variáveis de Ambiente

Crie um arquivo `.env` na raiz da pasta `mai_finance_flet/` (ou forneça as variáveis no ambiente / container):

```bash
# Supabase (obrigatório)
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY="sua-anon-key-aqui"

# Autenticação JWT (obrigatório - mesma chave usada no Next.js)
JWT_SECRET="seu-jwt-secret-com-minimo-32-caracteres"

# Porta do Servidor Web Flet (padrão: 8550)
FLET_PORT=8550
```

---

## 4. Como Executar Localmente

### Pré-requisitos
- Python 3.11 ou superior
- Ambiente virtual configurado

```powershell
# 1. Ativar o ambiente virtual
& "..\.venv\Scripts\Activate.ps1"

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o servidor Flet Web
flet run app.py --web --port 8550
# Ou diretamente:
python app.py
```

Acesse em seu navegador: `http://localhost:8550`.

---

## 5. Como Executar com Docker

### Build da Imagem
```bash
docker build -t mai-finance-flet:latest .
```

### Execução do Container
```bash
docker run -d \
  --name mai-finance-flet \
  -p 8550:8550 \
  --env-file .env \
  mai-finance-flet:latest
```

---

## 6. Execução da Suíte de Testes

Os testes automatizados cobrem todos os critérios de aceite (AC-001 a AC-020):

```powershell
& "..\.venv\Scripts\python.exe" -m pytest tests/ -v
```
