# 🚀 MAI Finance — Sistema de Gestão Financeira Inteligente

## 📊 Visão Geral
**MAI Finance** é uma plataforma moderna e completa de controle financeiro pessoal e empresarial. Projetada para proporcionar visualização clara da saúde financeira mensal, gestão de despesas por categoria, fechamento de ciclo e automações integradas.

---

## ✨ Funcionalidades do Sistema

### 💳 Gestão e Controle de Despesas
* **Lançamento de Despesas:** Cadastro detalhado com data de vencimento, dia de pagamento, categoria, valor, status (`pago` / `pendente`) e observações adicionais.
* **Categorização Personalizada:** Gerenciamento dinâmico de categorias com atribuição de cores hexadecimais para distinção visual intuitiva.
* **Visualização por Referência Mensal:** Filtro e agregação de gastos organizados pelo mês de referência (`month_ref`).
* **Resumo Financeiro em Tempo Real:** Cards dinâmicos e anéis de progresso que exibem o valor total acumulado, total pendente e quantidade de pendências do mês ativo.

### 🔄 Automação e Operações em Lote
* **Clonagem de Mês:** Duplicação automática de despesas recorrentes de um mês para outro com ajuste inteligente de datas.
* **Importação de Dados:** Suporte à carga em lote de lançamentos financeiros via arquivos estruturados.
* **Assistente Virtual Inteligente (AI Chat):** Widget interativo alimentado por IA (GROQ) para insights financeiros e análise de hábitos de gastos.

### 💾 Resiliência e Backups
* **Gerador de Snapshots de Backup:** Criação de snapshots completos (categorias e despesas) em formato `JSONB`.
* **Retenção Inteligente:** Execução automática via `pg_cron` (quinzenalmente) mantendo os 3 backups mais recentes para prevenção contra perda de dados.

---

## 🛡️ Características de Segurança & Proteção de Dados

### 🔒 Banco de Dados (Supabase) — estado atual
* **RLS habilitado** em todas as tabelas públicas, porém com políticas abertas (`TO public USING (true)`): o app acessa o Supabase com a *anon key* e não usa o Supabase Auth, então o isolamento real depende de quem conhece essa chave. Ver "Pendências de segurança" abaixo.
* **Isolamento de Aplicações:** tabela exclusiva (`mai_finance_users`) para não conflitar com outras aplicações no mesmo projeto Supabase.
* **Consultas parametrizadas** via cliente Supabase (sem SQL montado à mão).

### 🔐 Autenticação e Sessão
* **Senhas com PBKDF2-HMAC-SHA512** + salt aleatório de 16 bytes (compatível com os hashes do antigo Next.js). Senha mínima de 8 caracteres.
* **Sessão de 24 horas** com JWT HS256 assinado com `JWT_SECRET` (variável de ambiente; sem ela, um segredo aleatório é gerado e guardado no diretório de dados do app — nunca hard-coded).
* **"Manter conectado":** guarda apenas o e-mail e um token de 30 dias, que só serve para emitir uma nova sessão após confirmar que o usuário ainda existe. **A senha nunca é armazenada.** Logout apaga o token.
* **Isolamento de sessões no modo web:** no navegador a sessão fica no `localStorage` do próprio usuário; o servidor nunca grava sessões em disco (no Android/desktop o cache local fica no armazenamento do aparelho).

### 🔑 Segredos
* Nenhuma chave no código-fonte: `GROQ_API_KEY` vem do ambiente (web) ou é injetada pelo CI a partir de GitHub Secrets no build do APK.
* A keystore de assinatura do APK é lida dos secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_PASSWORD` e `ANDROID_KEY_ALIAS`. Enquanto eles não existirem, o CI usa a keystore legada do repositório e emite um aviso.

### ⚠️ Pendências de segurança
* As políticas RLS abertas permitem que qualquer pessoa com a *anon key* (presente no APK público) leia e altere os dados, inclusive os hashes de senha em `mai_finance_users`. Corrigir exige mover o acesso ao banco para trás de um backend (ex.: Edge Functions com a service role) ou migrar para o Supabase Auth com políticas por usuário.
* Credenciais que já estiveram no histórico público do repositório (chave Groq, keystore e sua senha) devem ser consideradas comprometidas e rotacionadas.

---

## 🛠️ Arquitetura e Tecnologia
* **Web App:** Python 3.11+, Flet (`mai_finance_flet/`), rodando como aplicação web (`ft.app(view=ft.AppView.WEB_BROWSER)`).
* **Design System & Responsividade:** Dark Mode Financeiro Elegante (com suporte a temas claro/escuro) e arquitetura de 3 breakpoints:
  - *Mobile (< 768px):* Coluna única, cabeçalho de 2 linhas, resumo em 2 níveis, botão flutuante (FAB) e cards de despesas.
  - *Compacto / Tablet (< 1024px):* Ações secundárias reunidas no menu de 3 pontinhos, busca adaptativa e lista em cards fluidos (sem esmagamento de colunas).
  - *Desktop Amplo (>= 1024px):* Tabela horizontal de 8 colunas com proteção contra quebra vertical de texto (`no_wrap=True`) e botões de atalho visíveis.
* **Autenticação:** PBKDF2-HMAC-SHA512, JWT HS256 de 24h e token de "manter conectado" de 30 dias.
* **Inteligência Artificial:** Groq SDK (`llama-3.3-70b-versatile`) com cache de respostas em memória.
* **Banco de Dados & Storage:** Supabase (PostgreSQL), `pg_cron`, RLS Policies.
* **Deploy:** Docker multi-stage com usuário não-root (`appuser`), porta 8550.

---

## 💻 Execução Local do Web App (Python + Flet)

### Executar a aplicação Flet Web:
```powershell
& ".\.venv\Scripts\python.exe" mai_finance_flet/app.py
```
Acesse no navegador: `http://localhost:8550`

### Executar a suíte completa de testes:
```powershell
& ".\.venv\Scripts\python.exe" -m pytest mai_finance_flet -v
```

---

## 🐳 Deploy via Docker

```bash
cd mai_finance_flet
docker build -t mai-finance-flet:latest .
docker run -d -p 8550:8550 --env-file .env mai-finance-flet:latest
```

---

## 📱 Instalador Android (APK) & Atualização Automática

O projeto conta com esteira de CI/CD 100% automatizada no GitHub Actions para compilação contínua e distribuição de atualizações do aplicativo Android.

### 🔄 Build Automático a Cada Commit:
- Sempre que um commit é enviado para o branch `main` com alterações no app (`mai_finance_flet/**`), o GitHub Actions compila o APK automaticamente.
- Cada compilação gera uma nova versão sequencial (`v1.0.{run_number}`) e disponibiliza o instalador na aba **Releases** do repositório.
- Também é possível disparar manualmente pela aba **Actions** selecionando versão customizada.

### 🚀 Auto-Update In-App (Atualização Automática no Celular):
1. **Identificação de Nova Versão:** Ao abrir o aplicativo no Android, o sistema verifica automaticamente a API do GitHub Releases em segundo plano.
2. **Modal Informativo:** Se houver versão mais recente, surge um diálogo elegante com as novidades e o botão **"Atualizar Agora"**.
3. **Download com Barra de Progresso:** O download do APK é realizado diretamente dentro do app com visualização em tempo real de porcentagem e MB baixados.
4. **Instalação com 1 Toque:** Ao concluir o download, o aplicativo abre imediatamente o instalador nativo do Android para aplicar a atualização preservando todos os dados locais.
5. **Checagem Manual:** No menu de configurações (ícone de 3 pontinhos no mobile ou botão no topo), toque em **"Verificar Atualizações"** a qualquer momento.
