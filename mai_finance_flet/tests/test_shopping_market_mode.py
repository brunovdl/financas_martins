"""
test_shopping_market_mode.py — Testes do Modo Mercado e finalização de compra (T-020).

Cobre os critérios de aceite:
- @spec:AC-026 — Interface do Modo Mercado por corredores e métricas de carrinho
- @spec:AC-029 — Conversão da compra em despesa no MAI Finance e arquivamento
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
import flet as ft

from ui.shopping_market_mode import ShoppingMarketModeView
from ui.components.shopping_finish_modal import open_shopping_finish_modal


class TestShoppingMarketMode:
    """Validação da interface no mercado e fechamento com despesa."""

    def test_market_mode_metrics_and_corridors_display(self):
        """Valida que o Modo Mercado agrupa por corredores e exibe totalizadores (AC-026)."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.client_storage = MagicMock()
        mock_page.client_storage.get.return_value = "dark"

        sample_items = [
            {"id": "1", "name": "Banana", "quantity": 1, "estimated_price": 8.0, "is_bought": True, "corridor_category": "Hortifruti"},
            {"id": "2", "name": "Maçã", "quantity": 1, "estimated_price": 10.0, "is_bought": False, "corridor_category": "Hortifruti"},
            {"id": "3", "name": "Sabão", "quantity": 2, "estimated_price": 20.0, "is_bought": True, "corridor_category": "Limpeza & Higiene"},
        ]

        with patch("ui.shopping_market_mode.get_all_items", return_value=sample_items), \
             patch("ui.shopping_market_mode.ShoppingRealtimeSync"):
            view = ShoppingMarketModeView(
                page=mock_page,
                market_name="Carrefour",
                on_exit_market_mode=MagicMock(),
            )
            view.did_mount()

            assert "48,00" in view.val_carrinho.value  # (8*1) + (20*2) = 48.0
            assert "2 de 3" in view.val_progresso.value
            assert view.btn_finish is not None

    def test_shopping_finish_modal_creates_expense_and_archives(self):
        """Valida conversão em despesa e arquivamento no fechamento da compra (AC-029)."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK

        bought_items = [
            {"id": "1", "name": "Arroz", "quantity": 1, "estimated_price": 30.0, "is_bought": True},
            {"id": "2", "name": "Feijão", "quantity": 2, "estimated_price": 10.0, "is_bought": True},
        ]

        with patch("ui.components.shopping_finish_modal.create_expense") as mock_create_exp, \
             patch("ui.components.shopping_finish_modal.save_shopping_history") as mock_save_hist, \
             patch("ui.components.shopping_finish_modal.clear_bought_items") as mock_clear, \
             patch("ui.components.shopping_finish_modal.list_categories", return_value=[{"id": "cat-1", "name": "Alimentação"}]):

            mock_create_exp.return_value = {"id": "exp-123", "amount": 50.0}
            on_completed = MagicMock()

            open_shopping_finish_modal(
                page=mock_page,
                bought_items=bought_items,
                market_name="Atacadão",
                total_calculated=50.0,
                on_completed=on_completed,
            )

            # Simula submissão do modal
            mock_dialog = mock_page.dialog if hasattr(mock_page, "dialog") else mock_page.show_dialog.call_args[0][0]
            # O botão de confirmação está dentro do conteúdo do diálogo
            btn_confirm = mock_dialog.content.content.controls[-1]
            btn_confirm.on_click(None)

            mock_create_exp.assert_called_once()
            call_args = mock_create_exp.call_args[0][0]
            assert call_args["amount"] == 50.0
            assert call_args["status"] == "pago"
            assert "Atacadão" in call_args["description"]

            mock_save_hist.assert_called_once()
            mock_clear.assert_called_once()
            on_completed.assert_called_once()
