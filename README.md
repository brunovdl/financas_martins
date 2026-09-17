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

### 🔒 Controle de Acesso e Isolamento no Banco de Dados (Row Level Security - RLS)
* **RLS Habilitado em Produção:** Todas as tabelas públicas (`mai_finance_users`, `categories`, `expenses`, `backups`) possuem **Row Level Security (RLS)** obrigatoriamente ativo no PostgreSQL/Supabase.
* **Políticas Estritas de Acesso (Policies):** Restrição total de acesso anônimo, permitindo operações de leitura e escrita apenas para requisições autenticadas (`TO authenticated`).
* **Isolamento de Aplicações:** Utilização de tabela exclusiva (`mai_finance_users`) para impedir qualquer interferência ou conflito de identidade com outras aplicações no mesmo projeto Supabase.

### 🔐 Arquitetura de Autenticação e Criptografia
* **Criptografia de Senhas (PBKDF2 + Salt):** Senhas armazenadas no banco utilizando o padrão de derivação de chave **PBKDF2** com *Salt* aleatório de 16 bytes e 1000 iterações em SHA-512.
* **Validação Estrita de Senha:** Imposição de senha mínima de 8 caracteres no cadastro e autenticação.
* **Proteção Contra Injeção e Manipulação:** Consultas parametrizadas via cliente Supabase prevenindo falhas de SQL Injection (CWE-89) e Acesso Indevido (CWE-284).

### ⏳ Gerenciamento de Sessão de 24 Horas & Tokens Criptografados
* **Cookies HTTP-Only & SameSite:** Armazenamento do token de sessão em cookies seguros com as diretivas `HttpOnly`, `SameSite=Lax` e `Path=/`, tornando o token inacessível para scripts maliciosos de terceiros no navegador (proteção contra XSS).
* **Expiração Rígida de 24 Horas:** O token de autenticação JWT assinado possui validade temporal de exatas 24 horas (`maxAge: 86400s`).
* **Deslogamento Automático:** Monitoramento contínuo da sessão. Ao atingir o limite de 24 horas, o sistema invalida a sessão, limpa os estados locais e exige nova autenticação.

---

## 🛠️ Arquitetura e Tecnologia
* **Web App:** Python 3.11+, Flet (`mai_finance_flet/`), rodando como aplicação web (`ft.app(view=ft.AppView.WEB_BROWSER)`).
* **Design System & Responsividade:** Dark Mode Financeiro Elegante (com suporte a temas claro/escuro) e arquitetura de 3 breakpoints:
  - *Mobile (< 768px):* Coluna única, cabeçalho de 2 linhas, resumo em 2 níveis, botão flutuante (FAB) e cards de despesas.
  - *Compacto / Tablet (< 1024px):* Ações secundárias reunidas no menu de 3 pontinhos, busca adaptativa e lista em cards fluidos (sem esmagamento de colunas).
  - *Desktop Amplo (>= 1024px):* Tabela horizontal de 8 colunas com proteção contra quebra vertical de texto (`no_wrap=True`) e botões de atalho visíveis.
* **Autenticação:** PBKDF2-HMAC-SHA512 e JWT HS256 (compatibilidade com usuários existentes).
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
