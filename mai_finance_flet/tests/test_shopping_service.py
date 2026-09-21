"""
test_shopping_service.py — Testes da lógica de negócios e resiliência offline (T-016).

Cobre os critérios de aceite:
- @spec:AC-021 — Adição de item com quantidade, unidade e corredor
- @spec:AC-022 — Sugestões e atalhos rápidos de itens frequentes
- @spec:AC-028 — Resiliência offline com sincronização automática
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from services.shopping_service import (
    add_shopping_item,
    get_corridors,
    get_items_grouped_by_corridor,
    calculate_cart_metrics,
    toggle_item_status,
    sync_offline_queue,
    get_pending_offline_count,
    get_quick_suggestions,
    _offline_mutation_queue,
)


class TestShoppingService:
    """Testes para o serviço de lista de compras e resiliência offline."""

    def setup_method(self):
        _offline_mutation_queue.clear()

    @patch("services.shopping_service.create_shopping_item")
    @patch("services.shopping_service.record_frequent_item_usage")
    def test_add_shopping_item_success(self, mock_record, mock_create):
        mock_create.return_value = {
            "id": "uuid-123",
            "name": "Leite Integral",
            "quantity": 2.0,
            "unit": "cx",
            "corridor_category": "Laticínios & Frios",
            "is_bought": False,
            "estimated_price": 5.50,
        }

        item = add_shopping_item("Leite Integral", 2, "cx", "Laticínios & Frios", 5.50)
        assert item["id"] == "uuid-123"
        assert item["name"] == "Leite Integral"
        assert item["quantity"] == 2.0
        assert item["corridor_category"] == "Laticínios & Frios"
        mock_record.assert_called_once_with("Leite Integral", "cx", "Laticínios & Frios")

    def test_add_shopping_item_empty_name_raises(self):
        with pytest.raises(ValueError, match="obrigatório"):
            add_shopping_item("   ")

    def test_get_corridors(self):
        corridors = get_corridors()
        assert "Hortifruti" in corridors
        assert "Laticínios & Frios" in corridors
        assert "Limpeza & Higiene" in corridors

    def test_calculate_cart_metrics(self):
        items = [
            {"id": "1", "name": "Item A", "quantity": 2, "estimated_price": 10.0, "is_bought": False},
            {"id": "2", "name": "Item B", "quantity": 1, "estimated_price": 20.0, "is_bought": True, "actual_price": 25.0},
            {"id": "3", "name": "Item C", "quantity": 3, "estimated_price": 5.0, "is_bought": True, "actual_price": None},
        ]
        metrics = calculate_cart_metrics(items)
        assert metrics["total_count"] == 3
        assert metrics["bought_count"] == 2
        assert metrics["pending_count"] == 1
        # Comprados: Item B (25.0 * 1) + Item C (5.0 * 3) = 40.0
        assert metrics["total_bought_amount"] == 40.0
        # Pendente: Item A (10.0 * 2) = 20.0
        assert metrics["total_pending_amount"] == 20.0
        assert metrics["completion_pct"] == round(2 / 3 * 100.0, 1)

    def test_group_items_by_corridor(self):
        items = [
            {"id": "1", "name": "Maçã", "corridor_category": "Hortifruti"},
            {"id": "2", "name": "Banana", "corridor_category": "Hortifruti"},
            {"id": "3", "name": "Sabão", "corridor_category": "Limpeza & Higiene"},
        ]
        grouped = get_items_grouped_by_corridor(items)
        assert len(grouped["Hortifruti"]) == 2
        assert len(grouped["Limpeza & Higiene"]) == 1
        assert "Bebidas" not in grouped  # Corredores vazios não aparecem

    @patch("services.shopping_service.toggle_item_bought")
    def test_toggle_item_status_online(self, mock_toggle):
        mock_toggle.return_value = {"id": "1", "is_bought": True}
        res = toggle_item_status("1", True)
        assert res["is_bought"] is True
        assert get_pending_offline_count() == 0

    @patch("services.shopping_service.update_shopping_item")
    @patch("services.shopping_service.toggle_item_bought")
    def test_toggle_item_status_offline_fallback_and_sync(self, mock_toggle, mock_update):
        # Simula falha de conexão 4G no supermercado
        mock_toggle.side_effect = ConnectionError("Sem sinal 4G")
        res = toggle_item_status("item-offline", True, actual_price=12.50)

        assert res["id"] == "item-offline"
        assert res["is_bought"] is True
        assert get_pending_offline_count() == 1

        # Agora a conexão é restabelecida
        mock_toggle.side_effect = None
        mock_toggle.return_value = {"id": "item-offline", "is_bought": True}
        mock_update.return_value = {"id": "item-offline", "actual_price": 12.50}

        synced = sync_offline_queue()
        assert synced == 1
        assert get_pending_offline_count() == 0

    @patch("services.shopping_service.list_frequent_items")
    def test_get_quick_suggestions_fallback(self, mock_list_freq):
        mock_list_freq.return_value = []
        suggestions = get_quick_suggestions()
        assert len(suggestions) > 0
        names = [s["name"] for s in suggestions]
        assert "Leite" in names
        assert "Café" in names
