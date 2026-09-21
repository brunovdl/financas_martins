# Tasks: Lista de Compras Inteligente

> feature: lista-compras

## T-015 — Modelagem das tabelas no Supabase (shopping_items, shopping_history, shopping_frequent_items) com RLS [concluida]
- Refs: US-010, US-013, AC-021, AC-029
- Arquivos: schema.sql, mai_finance_flet/db/shopping.py, mai_finance_flet/tests/test_shopping_db.py
- Esforço: medio
- Notas: Criar tabelas shopping_items (id, name, quantity, unit, corridor_category, is_bought, estimated_price, actual_price, market_name, created_at, updated_at), shopping_history (id, total_amount, market_name, items_count, items_snapshot, expense_id, closed_at), shopping_frequent_items (id, name, default_unit, corridor_category, usage_count). RLS habilitado com políticas authenticated. Funções de CRUD em shopping.py.

## T-016 — Serviço de gerenciamento de itens, atalhos rápidos e cache offline [concluida]
- Refs: US-010, US-012, AC-021, AC-022, AC-028
- Arquivos: mai_finance_flet/services/shopping_service.py, mai_finance_flet/tests/test_shopping_service.py
- Esforço: medio
- Notas: Implementar lógica de adição de itens com categoria de corredor, lista de sugestões frequentes com incremento de uso, marcação de 'OK' (is_bought) com persistência local em caso de perda de conexão (resiliência 4G) e sincronização pendente.

## T-017 — Módulo de geolocalização e cotação inteligente com Groq + Busca Web [concluida]
- Refs: US-011, AC-023, AC-024, AC-025
- Arquivos: mai_finance_flet/services/market_ai_service.py, mai_finance_flet/services/geo_service.py, mai_finance_flet/tests/test_market_ai.py
- Esforço: alto
- Notas: Obter geolocalização do dispositivo Android (fallback para CEP/cidade configurada). Identificar redes de supermercado locais (ex: Carrefour, Pão de Açúcar, etc.). Fazer busca web dos itens da lista e passar os resultados para o Groq (Llama 3.3) estruturar os preços unitários, marcas líderes com melhor custo-benefício e calcular o total estimado por mercado, permitindo fixar um mercado único para toda a lista.

## T-018 — Sincronização em tempo real via Supabase Realtime [concluida]
- Refs: US-012, AC-027
- Arquivos: mai_finance_flet/services/shopping_realtime.py, mai_finance_flet/tests/test_shopping_realtime.py
- Esforço: medio
- Notas: Configurar canal de Realtime no Supabase para escutar eventos INSERT/UPDATE/DELETE na tabela shopping_items, notificando a interface para atualização instantânea entre os dispositivos de Bruno e da esposa.

## T-019 — Interface da Lista de Compras: cadastro, corredores e cotação [concluida]
- Refs: US-010, US-011, AC-021, AC-022, AC-024, AC-025
- Arquivos: mai_finance_flet/ui/shopping_view.py, mai_finance_flet/ui/components/shopping_item_card.py, mai_finance_flet/ui/components/market_quote_modal.py, mai_finance_flet/tests/test_shopping_view.py
- Esforço: alto
- Notas: Construir a tela da Lista de Compras com campo de adição rápida, chips de atalhos frequentes, visualização dos itens agrupados por corredor e botão de cotação com IA exibindo o modal comparativo dos supermercados e seleção do mercado oficial.

## T-020 — Interface do Modo Mercado, métricas de carrinho e finalização com despesa [concluida]
- Refs: US-012, US-013, AC-026, AC-029
- Arquivos: mai_finance_flet/ui/shopping_market_mode.py, mai_finance_flet/ui/components/shopping_finish_modal.py, mai_finance_flet/tests/test_shopping_market_mode.py
- Esforço: alto
- Notas: Criar o Modo Mercado com alvos de toque grandes (mínimo 48px), indicador no topo de total acumulado do carrinho vs restante, e modal de finalização de compra que confirma o valor final do cupom fiscal, gera a despesa na tabela expenses (categoria Mercado, status pago) e arquiva os itens no histórico.

## T-021 — Visibilidade no Dashboard (card de pendências) e barra de navegação [concluida]
- Refs: US-014, AC-030
- Arquivos: mai_finance_flet/ui/dashboard_view.py, mai_finance_flet/ui/nav.py, mai_finance_flet/app.py, mai_finance_flet/tests/test_shopping_nav.py
- Esforço: medio
- Notas: Adicionar card de destaque no Dashboard informando a quantidade de itens pendentes na lista de compras com atalho de 1 toque, e adicionar a rota/destino na barra de navegação do app.
