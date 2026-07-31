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
* **Frontend & App Router:** Next.js (React), Tailwind CSS, Lucide Icons, TypeScript.
* **Design System:** Dark Mode Financeiro Elegante com suporte a temas responsivos.
* **Backend & API:** Next.js Server API Routes, Node.js Crypto.
* **Banco de Dados & Storage:** Supabase (PostgreSQL), `pg_cron`, RLS Policies.
