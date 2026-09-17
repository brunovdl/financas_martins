# Escopo e paridade

## Requisitos confirmados

1. Android implementado com Flet.
2. Uso pessoal por Bruno e esposa.
3. Todas as funcionalidades atuais da web acessíveis no celular.
4. Interface projetada para telas pequenas.
5. Telas e regras planejadas em Markdown antes do desenvolvimento.
6. Contas individuais para Bruno e esposa, com todas as despesas e categorias compartilhadas entre os dois (resposta P01).
7. Reutilizar os mesmos e-mails, senhas e identidades já existentes na web; nenhuma conta específica para Android.
8. Exibir e operar os mesmos dados da web, incluindo todos os meses, campos, categorias, backups e capacidades bancárias existentes. A organização visual pode mudar para funcionar bem no celular.
9. Consulta offline dos últimos dados carregados por mês (cache local com registro de data/hora do snapshot); mutações (criação, edição, exclusão, importação, clonagem, restauração) restritas ao modo online para evitar conflitos concorrentes (DEC-010).

## Matriz de cobertura

| Função existente | Referência web | Destino Android proposto | Observação |
| --- | --- | --- | --- |
| Entrar, cadastrar e sair | AuthPage, AuthContext, API auth | A01–A03, M01 | Mesmas contas existentes; cadastro usa o mesmo serviço da web |
| Verificar e expirar sessão | AuthContext, lib/auth | A00, A01, M01 | Manter a regra existente de 24 horas como base de paridade |
| Navegar entre meses | GastosApp | H01, D01, S01 | Preservar mês compartilhado entre telas financeiras |
| Total, pago, pendente e percentual | GastosApp, ProgressRing | H01 | Resumo do mês inteiro, independente dos filtros |
| Listar despesas e pesquisar descrição/categoria | GastosApp | D01 | Lista vertical com resumo por item |
| Filtrar pendentes | GastosApp | D01 | Filtro claramente ativo |
| Criar e editar todos os campos | GastosApp | D02, D03 | Campos opcionais acessíveis sem sobrecarregar a primeira tela |
| Marcar pago ou pendente | GastosApp | D01, D02 | Data de pagamento precisa de regra uniforme |
| Excluir uma despesa | GastosApp | D02, D04 | Confirmação mobile proposta |
| Selecionar várias, somar e excluir | GastosApp | D04 | Totais pagos e pendentes dos selecionados |
| Consultar pendências do mês anterior | GastosApp | H02 | Não confundir com todas as despesas vencidas |
| Criar, editar e excluir categorias e cores | CategoriesModal | C01–C03 | Excluir categoria preserva despesas |
| Importar XLSX, XLS e CSV | ImportModal | I01–I04 | Inclui múltiplas abas, mapeamento e distribuição por meses |
| Clonar mês | CloneMonthModal, GastosApp | L01, L02 | Todas as despesas, como pendentes e sem pagamento |
| Listar, criar e restaurar backups | BackupModal, supabaseClient | B01–B03 | Escopo global de categorias e despesas |
| Backup dias 1 e 15; retenção de três | schema.sql, supabaseClient | B01 + servidor | Deve funcionar com o celular fechado |
| Alternar tema claro/escuro | lib/theme, GastosApp | M01 | Tema do sistema é proposta adicional |
| Sincronização com Supabase | supabaseClient, GastosApp | Todas as telas de dados | Estados de atualização, falha e concorrência |
| Modo offline de consulta | GastosApp, SharedPreferences | Todas as telas de consulta | Cache local do snapshot mensal com data/hora; mutações apenas online (DEC-010) |
| Conversar com assistente | ChatWidget, API chat | Q01 | Contexto mensal, resumo e respostas em português |
| Consultar mês atual/outros meses/maior despesa | ChatWidget | Q01, Q02 | Resultados em cartões legíveis |
| Criar, editar e excluir despesas pelo chat | ChatWidget | Q03 | Confirmar conteúdo e mês antes da execução |
| Navegar para mês pelo chat | ChatWidget | Q01 → D01 | Manter o contexto de navegação consistente |
| Consultar contas, saldo, transações, fatura e fontes | API chat, cataCentavo | Q01, Q02 | Via chat garante a paridade; área bancária dedicada é opcional |
| Alterar categoria de transação bancária | API confirm-bank-action | Q03 | Confirmar e executar no servidor |

## Regras existentes a preservar ou decidir explicitamente

- Moeda BRL; idioma pt-BR. Banco usa `month_ref` no primeiro dia do mês; a interface usa ano/mês.
- Despesa tem vencimento, categoria opcional, descrição, valor, pagamento opcional, status e observação opcional.
- Status existentes: `pago` e `pendente`; não há receita, orçamento ou fechamento mensal persistido implementado.
- Lista ordenada pelo dia de vencimento. Os filtros não mudam os indicadores gerais do mês.
- Na tabela web, marcar pago coloca a data de hoje; voltar para pendente não limpa o pagamento. Edição pelo chat não reproduz automaticamente essa regra. Unificação pendente.
- Clonagem preserva descrição, valor, categoria e observação, ajusta o dia ao limite do destino e soma novos registros aos existentes. Não incrementa parcelas no texto nem detecta duplicatas.
- Importação: referência explícita > mês da data de vencimento > mês identificado na aba > mês selecionado. Categoria desconhecida vira Outros; `pago`/`paid` tornam-se pago, demais valores pendente.
- Backup contém todas as categorias e despesas; não contém usuários, extratos bancários ou histórico de chat. A restauração substitui os dados atuais.
- A interface usa categoria derivada do nome; o banco usa UUID. O app deve preservar a associação por identificador estável.

## Melhorias propostas, ainda não confirmadas

- Mensagens de sucesso somente após confirmação de persistência ou indicação explícita de operação aguardando sincronização, se offline for aprovado.
- Confirmação de exclusão, validação consistente de valores/datas e prevenção de envio duplicado.
- Armazenamento protegido da sessão no celular; biometria é melhoria opcional. A base mantém as 24 horas existentes, sem propor mudança de duração nesta etapa.
- Eventual área bancária dedicada, notificações e funcionamento offline dependem da entrevista.

Não reduzir importação, backup ou operações do chat a links para abrir a versão web.
