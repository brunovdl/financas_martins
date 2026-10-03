"""
test_shopping_view.py — Testes unitários para a view da lista de compras (T-019).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
import flet as ft

from ui.shopping_view import ShoppingView
from ui.components.shopping_add_item_modal import open_shopping_add_item_modal
from ui.components.shopping_location_modal import open_shopping_location_modal
from ui.components.shopping_quote_summary_modal import open_shopping_quote_summary_modal


class TestShoppingView:
    """Validação da interface da lista de compras e seus modais."""

    def test_shopping_view_init_and_render(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()
        mock_page.client_storage.get.return_value = "dark"
        mock_page.floating_action_button = None

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = [
                {"id": "1", "name": "Arroz 5kg", "quantity": 1, "corridor_category": "Mercearia & Padaria"},
                {"id": "2", "name": "Leite", "quantity": 2, "corridor_category": "Laticínios & Frios"},
            ]

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )
            view.did_mount()

            assert len(view.items) == 2
            assert view.market_banner is not None
            assert view.btn_market_mode is not None
            assert mock_page.floating_action_button is not None
            assert mock_page.floating_action_button.icon == ft.Icons.ADD

    def test_shopping_view_quick_chip_adds_item(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()
        mock_page.client_storage.get.return_value = None
        if hasattr(mock_page, "session"):
            mock_page.session.get.return_value = None

        with patch("ui.shopping_view.add_shopping_item") as mock_add, \
             patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.get_local_item", return_value=None), \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = []

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )

            view._add_quick_item("Café", "pct", "Mercearia & Padaria")
            mock_add.assert_called_once_with(
                name="Café", quantity=1.0, unit="pct", corridor="Mercearia & Padaria", market_name=None
            )

    def test_shopping_view_theme_toggle(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()
        mock_page.client_storage.get.return_value = "dark"

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"), \
             patch("ui.shopping_view.toggle_theme") as mock_toggle:
            mock_get_items.return_value = []
            mock_toggle.return_value = "light"

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )

            view._toggle_theme_view(None)
            assert view.theme_mode == "light"
            assert view.btn_theme.icon == ft.Icons.DARK_MODE_OUTLINED
            assert view.bgcolor == view.T["pageBg"]


    def test_shopping_view_location_and_market_update(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = []

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )

            view._on_location_saved("Belo Horizonte, MG", "Supermercados BH")
            assert "Belo Horizonte, MG" in view.market_city_label.value
            assert "Supermercados BH" in view.market_name_label.value
            assert view.selected_market == "Supermercados BH"

    def test_shopping_view_will_unmount_cleans_fab(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()
        mock_page.floating_action_button = MagicMock()

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = []

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )
            view.will_unmount()
            assert mock_page.floating_action_button is None


class TestShoppingModals:
    """Validação da inicialização segura dos diálogos e modais de compras."""

    def test_open_shopping_add_item_modal(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.show_dialog = MagicMock()

        callback_called = []
        open_shopping_add_item_modal(
            page=mock_page,
            on_item_added=lambda name: callback_called.append(name),
            current_market="Carrefour",
        )
        mock_page.show_dialog.assert_called_once()
        dlg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)

    def test_open_shopping_location_modal(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.show_dialog = MagicMock()

        open_shopping_location_modal(
            page=mock_page,
            current_city="São Paulo, SP",
            current_market=None,
            on_location_saved=lambda city, m: None,
        )
        mock_page.show_dialog.assert_called_once()
        dlg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)

    def test_open_shopping_quote_summary_modal(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.show_dialog = MagicMock()

        quote_data = {
            "markets": [
                {
                    "market_name": "Paulistão Atacadista",
                    "total_amount": 68.0,
                    "items": [
                        {"name": "Café 500g", "brand": "3 Corações", "quantity": 1, "unit": "pct", "unit_price": 18.0, "total_price": 18.0},
                        {"name": "Garrafa térmica", "brand": "Invicta", "quantity": 1, "unit": "un", "unit_price": 50.0, "total_price": 50.0},
                    ],
                }
            ]
        }

        applied = []
        open_shopping_quote_summary_modal(
            page=mock_page,
            market_name="Paulistão Atacadista",
            city="Araraquara",
            quote_data=quote_data,
            on_apply_prices=lambda m, items: applied.append((m, items)),
        )
        mock_page.show_dialog.assert_called_once()
        dlg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)
        assert dlg.content.width == 360

    def test_shopping_view_handle_toggle_bought(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()

        with patch("ui.shopping_view.update_shopping_item") as mock_update, \
             patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = []

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )
            view._handle_toggle_bought("item-99", True)
            mock_update.assert_called_once_with("item-99", {"is_bought": True})

    def test_shopping_item_card_checkbox_normal_mode(self):
        from ui.components.shopping_item_card import build_shopping_item_card

        toggled = []
        deleted = []
        item = {
            "id": "item-123",
            "name": "Café",
            "quantity": 1,
            "unit": "un",
            "corridor_category": "Mercearia & Padaria",
            "is_bought": False,
            "estimated_price": 18.0,
        }

        card = build_shopping_item_card(
            item=item,
            theme_mode="dark",
            on_delete=lambda it_id: deleted.append(it_id),
            on_toggle=lambda it_id, b: toggled.append((it_id, b)),
            is_market_mode=False,
        )

        # Layout em 2 linhas (DEC-030): row1 (checkbox + nome), row2 (preço + ações)
        column_rows = card.content.controls
        row1 = column_rows[0]
        row2 = column_rows[1]

        # Primeiro elemento da Linha 1: checkbox à esquerda
        btn_check = row1.controls[0]
        assert isinstance(btn_check, ft.IconButton)
        assert btn_check.icon == ft.Icons.CHECK_BOX_OUTLINE_BLANK

        # Último elemento da Linha 2: grupo de ações à direita contendo a lixeira
        actions_group = row2.controls[-1]
        if isinstance(actions_group, ft.Row):
            btn_delete = actions_group.controls[-1]
        else:
            btn_delete = actions_group
        assert isinstance(btn_delete, ft.IconButton)
        assert btn_delete.icon == ft.Icons.DELETE_OUTLINE

        # Simula clique no checkbox
        btn_check.on_click(None)
        assert toggled == [("item-123", True)]


    def test_shopping_view_progress_card_counts_and_total(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = [
                {"id": "1", "name": "Arroz", "quantity": 2, "estimated_price": 10.0, "is_bought": True},
                {"id": "2", "name": "Leite", "quantity": 1, "estimated_price": 5.0, "actual_price": 6.0},
                {"id": "3", "name": "Pão", "quantity": 1},
                {"id": "4", "name": "Café", "quantity": 1, "is_bought": False},
            ]

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )
            assert view.progress_card.visible is False

            view.load_data()

            assert view.progress_card.visible is True
            assert view.progress_count_text.value == "1/4 no carrinho"
            assert view.progress_bar.value == 0.25
            # 2 × 10,00 + 1 × 6,00 (preço real prevalece sobre o estimado)
            assert view.progress_total_value.value == "R$ 26,00"

    def test_shopping_view_collapse_and_expand_corridor(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()

        with patch("ui.shopping_view.get_all_items") as mock_get_items, \
             patch("ui.shopping_view.ShoppingRealtimeSync"):
            mock_get_items.return_value = [
                {"id": "1", "name": "Banana", "quantity": 1, "corridor_category": "Hortifruti", "is_bought": True},
                {"id": "2", "name": "Tomate", "quantity": 1, "corridor_category": "Hortifruti"},
                {"id": "3", "name": "Leite", "quantity": 1, "corridor_category": "Laticínios & Frios"},
            ]

            view = ShoppingView(
                page=mock_page,
                on_back_to_dashboard=MagicMock(),
                on_open_market_mode=MagicMock(),
            )
            view.load_data()
            expanded_count = len(view.items_list_col.controls)
            assert expanded_count == 5  # 2 cabeçalhos + 3 cards

            hortifruti_header = next(
                c for c in view.items_list_col.controls
                if isinstance(c.content, ft.Row)
                and any(isinstance(x, ft.Text) and x.value == "HORTIFRUTI" for x in c.content.controls)
            )
            # Contador de comprados/total no cabeçalho
            assert any(
                isinstance(x, ft.Container) and isinstance(x.content, ft.Text) and x.content.value == "1/2"
                for x in hortifruti_header.content.controls
            )

            # Recolhe Hortifruti: seus 2 cards somem, o cabeçalho permanece
            hortifruti_header.on_click(None)
            assert "Hortifruti" in view.collapsed_corridors
            assert len(view.items_list_col.controls) == 3

            # Estado recolhido sobrevive a uma recarga (ex.: sincronização em tempo real)
            view.load_data()
            assert len(view.items_list_col.controls) == 3

            # Expande novamente
            view._toggle_corridor("Hortifruti")
            assert len(view.items_list_col.controls) == expanded_count
