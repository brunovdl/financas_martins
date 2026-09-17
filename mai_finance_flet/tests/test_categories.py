"""
test_categories.py — Testes unitários para o serviço de categorias (T-006).

Cobre os critérios de aceite:
- @spec:AC-010 — Nome de categoria deve ser único
- @spec:AC-011 — Exclusão de categoria desvincula despesas sem apagá-las
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from services.categories import (
    list_categories,
    create_category,
    update_category,
    delete_category,
    get_category_by_name,
)


# ---------------------------------------------------------------------------
# AC-010: Unicidade do nome da categoria
# @spec:AC-010
# ---------------------------------------------------------------------------

class TestCategoryUniqueness:
    """@spec:AC-010 — Validação de nome único e criação de categorias."""

    def test_create_category_empty_name_raises(self):
        with pytest.raises(ValueError, match="obrigatório"):
            create_category("   ")

    def test_create_category_duplicate_name_raises(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.limit.return_value = mock_query
        # Simula que já existe uma categoria com este nome
        mock_query.execute.return_value = MagicMock(
            data=[{"id": "cat-1", "name": "Alimentação", "color": "#F2B84B"}]
        )

        with pytest.raises(ValueError, match="Já existe uma categoria"):
            create_category("Alimentação", color="#F2B84B", client=mock_client)

    def test_create_category_success(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.insert.return_value = mock_query

        # Primeira consulta (verificação de duplicidade): vazia
        # Segunda consulta (insert): retorna nova categoria
        mock_query.execute.side_effect = [
            MagicMock(data=[]),
            MagicMock(data=[{"id": "new-cat-1", "name": "Educação", "color": "#5EA8F2"}]),
        ]

        result = create_category("Educação", color="#5EA8F2", client=mock_client)
        assert result["id"] == "new-cat-1"
        assert result["name"] == "Educação"
        assert result["color"] == "#5EA8F2"

        # Garante que o payload usa 'color' (não color_hex, type ou icon)
        insert_payload = mock_query.insert.call_args[0][0]
        assert "color" in insert_payload
        assert insert_payload["color"] == "#5EA8F2"
        assert "type" not in insert_payload
        assert "icon" not in insert_payload

    def test_update_category_duplicate_name_raises(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.limit.return_value = mock_query
        # Simula que outra categoria diferente já usa esse nome
        mock_query.execute.return_value = MagicMock(
            data=[{"id": "cat-2", "name": "Moradia", "color": "#3FD6C4"}]
        )

        with pytest.raises(ValueError, match="Já existe uma categoria"):
            update_category("cat-1", "Moradia", color="#3FD6C4", client=mock_client)


# ---------------------------------------------------------------------------
# AC-011: Exclusão desvincula despesas sem apagá-las
# @spec:AC-011
# ---------------------------------------------------------------------------

class TestCategoryDeletion:
    """@spec:AC-011 — Exclusão de categoria desvincula despesas (category_id = NULL)."""

    def test_delete_category_unlinks_expenses_and_removes_category(self):
        mock_client = MagicMock()
        mock_expenses_query = MagicMock()
        mock_categories_query = MagicMock()

        def table_router(table_name: str):
            if table_name == "expenses":
                return mock_expenses_query
            return mock_categories_query

        mock_client.table.side_effect = table_router
        mock_expenses_query.update.return_value = mock_expenses_query
        mock_expenses_query.eq.return_value = mock_expenses_query
        mock_expenses_query.execute.return_value = MagicMock(data=[])

        mock_categories_query.delete.return_value = mock_categories_query
        mock_categories_query.eq.return_value = mock_categories_query
        mock_categories_query.execute.return_value = MagicMock(data=[{"id": "cat-del-1"}])

        assert delete_category("cat-del-1", client=mock_client)

        # 1. Verifica desvinculação em expenses
        mock_expenses_query.update.assert_called_once_with({"category_id": None})
        mock_expenses_query.eq.assert_called_once_with("category_id", "cat-del-1")

        # 2. Verifica exclusão em categories
        mock_categories_query.delete.assert_called_once()
        mock_categories_query.eq.assert_called_once_with("id", "cat-del-1")


# ---------------------------------------------------------------------------
# Listagem de Categorias
# ---------------------------------------------------------------------------

class TestListCategories:
    def test_list_categories_ordered_by_name(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {"id": "cat-1", "name": "Alimentação", "color": "#F2B84B"},
                {"id": "cat-2", "name": "Transporte", "color": "#3FD6C4"},
            ]
        )

        res = list_categories(client=mock_client)
        assert len(res) == 2
        mock_client.table.assert_called_with("categories")
        mock_query.order.assert_called_with("name")
