"""
test_clone_month.py — Testes unitários para a funcionalidade de clonagem de mês (T-007).

Cobre o critério de aceite:
- @spec:AC-012 — Clonagem ajusta due_date e reseta status
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from services.clone_month import calculate_cloned_due_date, clone_month


# ---------------------------------------------------------------------------
# AC-012: Cálculo de datas e truncamento no mês destino
# @spec:AC-012
# ---------------------------------------------------------------------------

class TestCloneMonthDateCalculation:
    """@spec:AC-012 — Ajuste de due_date mantendo dia ou ajustando para o fim do mês."""

    def test_same_day_copied_when_exists(self):
        # 15 de abril -> 15 de maio
        assert calculate_cloned_due_date("2026-04-15", "2026-05") == "2026-05-15"
        # 05 de janeiro -> 05 de fevereiro
        assert calculate_cloned_due_date("2026-01-05", "2026-02") == "2026-02-05"

    def test_day_31_clamped_to_last_day_of_february(self):
        # Ano não bissexto: 31 Jan -> 28 Fev
        assert calculate_cloned_due_date("2026-01-31", "2026-02") == "2026-02-28"
        # Ano bissexto: 31 Jan -> 29 Fev
        assert calculate_cloned_due_date("2024-01-31", "2024-02") == "2024-02-29"

    def test_day_31_clamped_to_day_30_in_30_day_months(self):
        # 31 de maio -> 30 de junho
        assert calculate_cloned_due_date("2026-05-31", "2026-06") == "2026-06-30"
        # 31 de agosto -> 30 de setembro
        assert calculate_cloned_due_date("2026-08-31", "2026-09") == "2026-09-30"


# ---------------------------------------------------------------------------
# AC-012: Clonagem de lançamentos
# @spec:AC-012
# ---------------------------------------------------------------------------

class TestCloneMonthService:
    """@spec:AC-012 — Clonagem com reset de status e month_ref correto."""

    def test_clone_same_month_raises_value_error(self):
        with pytest.raises(ValueError, match="diferentes"):
            clone_month("2026-05", "2026-05")

    def test_clone_empty_source_returns_empty_list(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[])

        result = clone_month("2026-01", "2026-02", client=mock_client)
        assert result == []

    def test_clone_expenses_resets_status_and_adjusts_dates(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.insert.return_value = mock_query

        source_data = [
            {
                "id": "exp-orig-1",
                "description": "Aluguel",
                "amount": 2500.0,
                "due_date": "2026-01-10",
                "category_id": "cat-uuid-1",
                "status": "pago",
                "payment_date": "2026-01-09",
                "observation": "Pix proprietário",
                "month_ref": "2026-01-01",
            },
            {
                "id": "exp-orig-2",
                "description": "Internet",
                "amount": 120.0,
                "due_date": "2026-01-31",
                "category_id": None,
                "status": "pago",
                "payment_date": "2026-01-30",
                "observation": None,
                "month_ref": "2026-01-01",
            },
        ]

        # 1ª chamada: leitura das despesas originais
        # 2ª chamada: inserção do lote clonado
        mock_query.execute.side_effect = [
            MagicMock(data=source_data),
            MagicMock(data=[{"id": "cloned-1"}, {"id": "cloned-2"}]),
        ]

        cloned_result = clone_month("2026-01", "2026-02", client=mock_client)
        assert len(cloned_result) == 2

        # Inspeciona os payloads gerados para o insert
        inserted_payloads = mock_query.insert.call_args[0][0]
        assert len(inserted_payloads) == 2

        item1 = inserted_payloads[0]
        assert item1["description"] == "Aluguel"
        assert item1["amount"] == 2500.0
        assert item1["due_date"] == "2026-02-10"
        assert item1["category_id"] == "cat-uuid-1"
        assert item1["status"] == "pendente"        # resetado
        assert item1["payment_date"] is None        # nulo
        assert item1["month_ref"] == "2026-02-01"

        item2 = inserted_payloads[1]
        assert item2["description"] == "Internet"
        assert item2["amount"] == 120.0
        assert item2["due_date"] == "2026-02-28"    # 31 jan -> 28 fev clamp
        assert item2["status"] == "pendente"
        assert item2["payment_date"] is None
        assert item2["month_ref"] == "2026-02-01"


# ---------------------------------------------------------------------------
# Testes de UI do Modal de Clonagem de Mês
# ---------------------------------------------------------------------------

class TestCloneMonthModalUI:
    """Valida inicialização, formatação de opções e validação do CloneMonthModal."""

    def test_modal_initialization_defaults(self):
        import flet as ft
        from ui.clone_month_modal import CloneMonthModal

        mock_page = MagicMock(spec=ft.Page)
        modal = CloneMonthModal(page=mock_page, current_month_ref="2026-09-01")

        # Verifica normalização para 'AAAA-MM'
        assert modal.current_month_ref == "2026-09"
        assert modal.from_month == "2026-09"
        assert modal.to_month == "2026-10"
        assert modal.from_dropdown.value == "2026-09"
        assert modal.to_dropdown.value == "2026-10"
        assert modal.from_dropdown.width == 330
        assert modal.to_dropdown.width == 330

    def test_modal_same_month_validation_prevents_clone(self):
        import flet as ft
        from ui.clone_month_modal import CloneMonthModal

        mock_page = MagicMock(spec=ft.Page)
        modal = CloneMonthModal(page=mock_page, current_month_ref="2026-09")
        modal.from_dropdown.value = "2026-09"
        modal.to_dropdown.value = "2026-09"

        modal._handle_clone(MagicMock())

        assert modal.error_text.visible is True
        assert "iguais" in modal.error_text.value.lower()
        mock_page.update.assert_called()
