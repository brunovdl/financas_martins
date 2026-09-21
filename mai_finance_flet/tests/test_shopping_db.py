"""
test_shopping_db.py — Testes unitários para a camada de persistência de compras (T-015).
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from db.shopping import (
    list_shopping_items,
    create_shopping_item,
    update_shopping_item,
    delete_shopping_item,
    toggle_item_bought,
    save_shopping_history,
    list_shopping_history,
    list_frequent_items,
    record_frequent_item_usage,
)


class TestShoppingDB:
    """Validação das operações de banco de dados para a lista de compras."""

    @patch("db.shopping.get_client")
    def test_create_shopping_item(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table

        created_record = {
            "id": "11111111-2222-3333-4444-555555555555",
            "name": "Leite Integral",
            "quantity": 2.0,
            "unit": "cx",
            "corridor_category": "Laticínios",
            "is_bought": False,
            "estimated_price": 5.49,
            "actual_price": None,
            "market_name": None,
        }
        mock_table.insert.return_value.execute.return_value.data = [created_record]

        result = create_shopping_item({
            "name": "Leite Integral",
            "quantity": 2,
            "unit": "cx",
            "corridor_category": "Laticínios",
            "estimated_price": 5.49,
        })

        assert result["name"] == "Leite Integral"
        assert result["quantity"] == 2.0
        assert result["corridor_category"] == "Laticínios"
        mock_table.insert.assert_called_once()

    @patch("db.shopping.get_client")
    def test_list_shopping_items(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.order.return_value = mock_table

        mock_data = [
            {"id": "item-1", "name": "Maçã", "corridor_category": "Hortifruti"},
            {"id": "item-2", "name": "Queijo", "corridor_category": "Laticínios"},
        ]
        mock_table.order.return_value.execute.return_value.data = mock_data

        items = list_shopping_items()
        assert len(items) == 2
        assert items[0]["name"] == "Maçã"

    @patch("db.shopping.get_client")
    def test_toggle_item_bought(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table

        mock_table.eq.return_value.execute.return_value.data = [
            {"id": "item-1", "name": "Maçã", "is_bought": True}
        ]

        res = toggle_item_bought("item-1", True)
        assert res["is_bought"] is True
        mock_table.update.assert_called_with({"is_bought": True})

    @patch("db.shopping.get_client")
    def test_delete_shopping_item(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value.execute.return_value.data = [{"id": "item-1"}]

        success = delete_shopping_item("item-1")
        assert success is True

    @patch("db.shopping.get_client")
    def test_save_and_list_history(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table

        mock_table.insert.return_value.execute.return_value.data = [
            {"id": "hist-1", "total_amount": 250.0}
        ]
        res = save_shopping_history(250.0, "Carrefour", 10, [{"name": "Item"}])
        assert res["id"] == "hist-1"

        mock_table.select.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value.execute.return_value.data = [
            {"id": "hist-1", "total_amount": 250.0}
        ]
        history = list_shopping_history(limit=5)
        assert len(history) == 1

    @patch("db.shopping.get_client")
    def test_frequent_items_record_and_list(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table

        # Novo item
        mock_table.select.return_value = mock_table
        mock_table.ilike.return_value.execute.return_value.data = []
        record_frequent_item_usage("Banana", "kg", "Hortifruti")
        mock_table.insert.assert_called_once()

        # Item existente
        mock_table.ilike.return_value.execute.return_value.data = [{"id": "freq-1", "usage_count": 3}]
        record_frequent_item_usage("Banana", "kg", "Hortifruti")
        mock_table.update.assert_called_with({
            "usage_count": 4,
            "default_unit": "kg",
            "corridor_category": "Hortifruti",
        })
