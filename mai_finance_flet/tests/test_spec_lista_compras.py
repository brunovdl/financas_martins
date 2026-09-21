# Testes de spec da feature lista-compras — gerados por onp-spec scaffold
import pytest

# US-010 — Gestão da Lista de Compras Compartilhada e Itens Frequentes
from unittest.mock import MagicMock, patch

def test_ac_021():
    """AC-021: Adição de item com quantidade, unidade e corredor @spec:AC-021"""
    from services.shopping_service import add_shopping_item, get_items_grouped_by_corridor

    with patch("services.shopping_service.create_shopping_item") as mock_create, \
         patch("services.shopping_service.record_frequent_item_usage"):
        mock_create.return_value = {
            "id": "item-ac-021",
            "name": "Leite Integral",
            "quantity": 2.0,
            "unit": "cx",
            "corridor_category": "Laticínios & Frios",
            "is_bought": False,
            "estimated_price": 5.49,
        }
        item = add_shopping_item("Leite Integral", 2.0, "cx", "Laticínios & Frios", 5.49)
        assert item["name"] == "Leite Integral"
        assert item["quantity"] == 2.0
        assert item["is_bought"] is False
        assert item["corridor_category"] == "Laticínios & Frios"

        grouped = get_items_grouped_by_corridor([item])
        assert "Laticínios & Frios" in grouped
        assert grouped["Laticínios & Frios"][0]["name"] == "Leite Integral"


def test_ac_022():
    """AC-022: Sugestões e atalhos rápidos de itens frequentes @spec:AC-022"""
    from services.shopping_service import get_quick_suggestions

    suggestions = get_quick_suggestions()
    assert len(suggestions) > 0
    names = [s["name"] for s in suggestions]
    assert "Café" in names
    assert "Arroz" in names
    assert any(s["corridor"] for s in suggestions)

# US-011 — Cotação da Lista Completa com IA e Supermercados Regionais
def test_ac_023():
    """AC-023: Detecção de localização para consulta de mercados da região @spec:AC-023"""
    from services.geo_service import get_device_location, get_regional_markets

    loc = get_device_location()
    assert "city" in loc
    assert loc["city"] != ""

    markets = get_regional_markets(loc["city"])
    assert len(markets) >= 2
    assert any(m["name"] for m in markets)


# US-011 — Cotação da Lista Completa com IA e Supermercados Regionais
def test_ac_024():
    """AC-024: Cotação comparativa e seleção de mercado único para a compra @spec:AC-024"""
    from services.market_ai_service import quote_shopping_list

    items = [
        {"id": "it-1", "name": "Arroz 5kg", "quantity": 1, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
        {"id": "it-2", "name": "Feijão 1kg", "quantity": 2, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
    ]
    quote_res = quote_shopping_list(items)
    assert len(quote_res["markets"]) >= 2
    assert "best_option" in quote_res
    assert quote_res["best_option"] in [m["market_name"] for m in quote_res["markets"]]
    # Valida que cada mercado tem o total do carrinho calculado para permitir seleção única
    for m in quote_res["markets"]:
        assert m["total_amount"] > 0
        assert len(m["items"]) == 2


# US-011 — Cotação da Lista Completa com IA e Supermercados Regionais
def test_ac_025():
    """AC-025: Priorização de melhor custo-benefício em marcas conhecidas @spec:AC-025"""
    from services.market_ai_service import _get_reference_item

    ref_arroz = _get_reference_item("Arroz 5kg")
    assert ref_arroz["brand"] in ["Camil / Tio João", "Camil", "Tio João"]
    assert ref_arroz["price"] > 0

    ref_cafe = _get_reference_item("Café torrado")
    assert "Pilão" in ref_cafe["brand"] or "Melitta" in ref_cafe["brand"]

# US-012 — Modo Mercado, Sincronização Realtime e Resiliência Offline
def test_ac_026():
    """AC-026: Interface do Modo Mercado por corredores e métricas de carrinho @spec:AC-026"""
    import flet as ft
    from ui.shopping_market_mode import ShoppingMarketModeView

    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.DARK
    mock_page.client_storage = MagicMock()
    mock_page.client_storage.get.return_value = "dark"

    items = [
        {"id": "1", "name": "Alface", "quantity": 1, "estimated_price": 5.0, "is_bought": True, "corridor_category": "Hortifruti"},
        {"id": "2", "name": "Tomate", "quantity": 1, "estimated_price": 8.0, "is_bought": False, "corridor_category": "Hortifruti"},
    ]

    with patch("ui.shopping_market_mode.get_all_items", return_value=items), \
         patch("ui.shopping_market_mode.ShoppingRealtimeSync"):
        view = ShoppingMarketModeView(
            page=mock_page,
            market_name="Pão de Açúcar",
            on_exit_market_mode=MagicMock(),
        )
        view.did_mount()

        assert "5,00" in view.val_carrinho.value
        assert "1 de 2" in view.val_progresso.value
        assert len(view.items_col.controls) >= 2


# US-013 — Finalização da Compra e Integração Financeira Automática
def test_ac_029():
    """AC-029: Conversão da compra em despesa no MAI Finance e arquivamento @spec:AC-029"""
    import flet as ft
    from ui.components.shopping_finish_modal import open_shopping_finish_modal

    mock_page = MagicMock(spec=ft.Page)
    mock_page.theme_mode = ft.ThemeMode.DARK

    bought = [{"id": "1", "name": "Café", "quantity": 1, "estimated_price": 18.0, "is_bought": True}]

    with patch("ui.components.shopping_finish_modal.create_expense") as mock_exp, \
         patch("ui.components.shopping_finish_modal.save_shopping_history") as mock_hist, \
         patch("ui.components.shopping_finish_modal.clear_bought_items") as mock_clear, \
         patch("ui.components.shopping_finish_modal.list_categories", return_value=[{"id": "cat-1", "name": "Mercado"}]):

        mock_exp.return_value = {"id": "exp-final"}
        completed_called = []

        open_shopping_finish_modal(
            page=mock_page,
            bought_items=bought,
            market_name="Carrefour",
            total_calculated=18.0,
            on_completed=lambda: completed_called.append(True),
        )

        mock_dlg = mock_page.dialog if hasattr(mock_page, "dialog") else mock_page.show_dialog.call_args[0][0]
        btn_confirm = mock_dlg.content.content.controls[-1]
        btn_confirm.on_click(None)

        mock_exp.assert_called_once()
        exp_payload = mock_exp.call_args[0][0]
        assert exp_payload["amount"] == 18.0
        assert exp_payload["status"] == "pago"
        assert "Carrefour" in exp_payload["description"]

        mock_hist.assert_called_once()
        mock_clear.assert_called_once()
        assert len(completed_called) == 1

# US-012 — Modo Mercado, Sincronização Realtime e Resiliência Offline
def test_ac_027():
    """AC-027: Sincronização em tempo real entre celulares via Supabase Realtime @spec:AC-027"""
    import time
    from services.shopping_realtime import ShoppingRealtimeSync

    received_updates = []
    with patch("services.shopping_realtime.list_shopping_items") as mock_list:
        mock_list.return_value = [{"id": "item-1", "name": "Leite", "is_bought": False}]
        sync = ShoppingRealtimeSync(on_change_callback=lambda items: received_updates.append(items), interval_seconds=0.02)
        sync.start()

        time.sleep(0.05)
        # Esposa marca OK no outro celular
        mock_list.return_value = [{"id": "item-1", "name": "Leite", "is_bought": True}]
        time.sleep(0.08)
        sync.stop()

        assert len(received_updates) >= 1
        assert received_updates[-1][0]["is_bought"] is True

# US-012 — Modo Mercado, Sincronização Realtime e Resiliência Offline
def test_ac_028():
    """AC-028: Resiliência offline com sincronização automática @spec:AC-028"""
    from services.shopping_service import toggle_item_status, sync_offline_queue, get_pending_offline_count, _offline_mutation_queue

    _offline_mutation_queue.clear()
    with patch("services.shopping_service.toggle_item_bought") as mock_toggle, \
         patch("services.shopping_service.update_shopping_item") as mock_update:
        # Simula erro de rede/timeout 4G
        mock_toggle.side_effect = ConnectionError("Falha de rede móvel")
        res = toggle_item_status("item-4g-offline", True)
        assert res["is_bought"] is True
        assert get_pending_offline_count() == 1

        # Reconexão de rede
        mock_toggle.side_effect = None
        mock_toggle.return_value = {"id": "item-4g-offline", "is_bought": True}
        mock_update.return_value = {"id": "item-4g-offline"}

        synced = sync_offline_queue()
        assert synced == 1
        assert get_pending_offline_count() == 0

# US-014 — Visibilidade no Dashboard Principal e Navegação
def test_ac_030():
    """AC-030: Card de compras no Dashboard e destino na barra de navegação @spec:AC-030"""
    import flet as ft
    from ui.dashboard_view import DashboardView
    from ui.nav import create_bottom_nav_bar

    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 1024
    nav_callbacks = []
    opened_shopping = []

    # Dado: que há itens pendentes na lista de compras
    pending_items = [
        {"id": "it-1", "name": "Sabão em pó", "is_bought": False},
        {"id": "it-2", "name": "Detergente", "is_bought": False},
        {"id": "it-3", "name": "Esponja", "is_bought": True},
    ]

    # Quando: o usuário visualiza o Dashboard principal
    with patch("db.shopping.list_shopping_items", return_value=pending_items):
        view = DashboardView(
            page=mock_page,
            on_open_shopping=lambda: opened_shopping.append(True),
        )
        view._update_shopping_card_ui()

        # Então: vê um card destacado indicando a quantidade de itens pendentes na lista com atalho direto
        assert hasattr(view, "card_shopping")
        assert view.card_shopping is not None
        assert "2 pendentes" in view.card_shopping_badge.value
        assert "2 itens" in view.card_shopping_val.value

        # Atalho direto via clique no ícone do cabeçalho
        assert hasattr(view, "btn_shopping_header_box")
        assert view.btn_shopping_header_box in view.account_row.controls
        view.btn_shopping_header_box.on_click(None)
        assert len(opened_shopping) == 1

        # Então: pode acessar a tela completa de Lista de Compras através da barra de navegação inferior
        nav_bar = create_bottom_nav_bar(
            on_change_tab=lambda idx: nav_callbacks.append(idx),
            selected_index=0,
            include_shopping=True,
        )
        compras_dest = [d for d in nav_bar.destinations if d.label == "Compras"]
        assert len(compras_dest) == 1
        assert compras_dest[0].icon == ft.Icons.SHOPPING_BAG_OUTLINED

        # Clique na aba Compras
        nav_bar.on_change(MagicMock(data="2"))
        assert nav_callbacks == [2]
