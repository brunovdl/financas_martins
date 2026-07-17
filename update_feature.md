# Especificação da Feature: Importação Dinâmica por Mês da Despesa

## 1. Visão Geral
Atualmente, ao importar uma planilha no sistema, todas as despesas importadas são atribuídas ao mês de referência atualmente selecionado na interface (`monthRef`). 

A melhoria solicitada visa permitir que o sistema **identifique automaticamente o mês correspondente de cada registro** (a partir de datas no formato completo como `DD/MM/YYYY`, `YYYY-MM-DD` ou campos de mês/ano) e atribua cada registro ao seu respectivo `month_ref` (ex: `2026-04`, `2026-05`).

---

## 2. Status
- Modo: `/grill-me` (Entrevista finalizada com sucesso)
- Arquivo criado na raiz do projeto: `update_feature.md`

---

## 3. Pontos de Decisão (Design Tree)

### Decisão 1: Identificação do Mês e Fallback
- **Definição**: Quando a data for completa (`DD/MM/YYYY`, `YYYY-MM-DD` ou data serial do Excel), o sistema extrai o mês e ano do próprio registro (ex: `2026-04`). Se a célula contiver apenas o dia (ex: `5` ou `05`), o sistema utilizará o mês/ano atualmente selecionado na tela (`monthRef`) como fallback.

### Decisão 2: Visualização na Pré-visualização (Preview)
- **Definição**: Na tabela da etapa de pré-visualização, haverá uma coluna explícita "Mês Ref" indicando o mês/ano de destino de cada linha (ex: `04/2026`). No topo do modal, será exibido um pequeno resumo/chips com a contagem de despesas agrupadas por mês (ex: `Abr/2026: 12 itens`, `Mai/2026: 5 itens`).

### Decisão 3: Comportamento da Aplicação e Atualização do Estado Pós-Importação
- **Definição**: Todos os registros importados serão salvos no banco de dados (Supabase) ou no estado local com seus respectivos valores de `month_ref`. A tela principal continuará exibindo o mês atualmente selecionado pelo usuário, e um toast/notificação de sucesso será exibido no topo (ex: *"15 despesas importadas com sucesso em 2 meses (Abril/2026, Maio/2026)"*).

### Decisão 4: Suporte a Coluna Dedicada de Mês/Ano
- **Definição**: O modal de mapeamento terá um novo campo opcional chamado `month_ref` ("Mês Ref").
  - Caso a planilha possua essa coluna (ex: valores como `04/2026`, `2026-04`, `Abril/2026`), ela terá prioridade na definição do mês da despesa.
  - Caso não esteja mapeada, a inferência será feita pela coluna de `vencimento` (se contiver data completa `DD/MM/YYYY` / `YYYY-MM-DD` / Date Excel).
  - Se nenhuma das opções fornecer mês/ano completo, o sistema utilizará o mês selecionado na aplicação (`monthRef`) como fallback.

---

## 4. Plano de Alterações Técnicas

1. **`components/ImportModal.tsx`**:
   - Adicionar o campo opcional `{ key: 'month_ref', label: 'Mês/Ano Ref', required: false, hint: 'ex: 04/2026, 2026-04 ou Abril/2026' }` em `IMPORT_FIELDS`.
   - Adicionar aliases de mapeamento para `month_ref` (`mes`, `mês`, `mes ref`, `mês ref`, `referencia`, `referência`, `month_ref`).
   - Atualizar `parseDateField` para retornar tanto o dia do mês (`dueDay`) quanto o mês de referência inferido (`inferredMonthRef`).
   - Adicionar função auxiliar `parseMonthRef(raw, fallback)` para extrair ano e mês de formatos textuais/numéricos de mês.
   - Atualizar `buildPreview` para utilizar o `monthRef` derivado de cada linha.
   - Atualizar a interface do modal de pré-visualização para incluir a coluna "Mês Ref" na tabela e os cards de resumo por mês no topo.

2. **`components/GastosApp.tsx`**:
   - Atualizar `handleImportRows` para lidar com inserções multi-mês no Supabase/Estado local.
   - Adicionar estado e renderização do Toast de sucesso pós-importação informando total de itens e meses impactados.
