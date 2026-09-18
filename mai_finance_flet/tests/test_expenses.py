"""
test_expenses.py — Testes unitários para o serviço de despesas.
Cobre: AC-005, AC-006, AC-007, AC-008, AC-009.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-32-bytes-long!")

from services.expenses import (
    month_ref_to_date,
    date_to_month_ref,
    list_expenses,
    get_monthly_summary,
    create_expense,
    update_expense,
    delete_expense,
    delete_expenses_batch,
    toggle_expense_status,
)


class TestExpensesHelpers:
    def test_month_ref_conversions(self):
        assert month_ref_to_date("2026-09") == "2026-09-01"
        assert month_ref_to_date("2026-09-01") == "2026-09-01"
        assert date_to_month_ref("2026-09-01") == "2026-09"
        assert date_to_month_ref("2026-09-15") == "2026-09"


class TestListExpenses:
    """AC-005: Listagem filtrada por month_ref e ordenada por due_date."""

    def test_list_expenses_filters_by_month_ref(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {"id": "exp-1", "description": "Internet", "due_date": "2026-09-10", "month_ref": "2026-09-01"},
                {"id": "exp-2", "description": "Aluguel", "due_date": "2026-09-15", "month_ref": "2026-09-01"},
            ]
        )

        res = list_expenses("2026-09", client=mock_client)
        assert len(res) == 2
        mock_client.table.assert_called_with("expenses")
        mock_query.eq.assert_called_with("month_ref", "2026-09-01")
        mock_query.order.assert_any_call("due_date", desc=False)
        mock_query.order.assert_any_call("created_at", desc=False)
        mock_query.order.assert_any_call("id", desc=False)


class TestMonthlySummary:
    """AC-006, AC-007: Resumo mensal e proporção de pagamento."""

    def test_get_monthly_summary_from_view(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{
                "month_ref": "2026-09-01",
                "total_despesas": 5000.0,
                "total_pendente": 2000.0,
                "qtd_pendente": 3,
            }]
        )

        summary = get_monthly_summary("2026-09", client=mock_client)
        assert summary["total_despesas"] == 5000.0
        assert summary["total_pendente"] == 2000.0
        assert summary["total_pago"] == 3000.0
        assert summary["qtd_pendente"] == 3
        assert summary["percent_pago"] == 60.0

    def test_get_monthly_summary_empty(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[])

        summary = get_monthly_summary("2026-09", client=mock_client)
        assert summary["total_despesas"] == 0.0
        assert summary["total_pendente"] == 0.0
        assert summary["total_pago"] == 0.0
        assert summary["qtd_pendente"] == 0
        assert summary["percent_pago"] == 100.0


class TestExpenseCRUD:
    """AC-008: Criação, edição e exclusão de despesas."""

    def test_create_expense_validation(self):
        with pytest.raises(ValueError, match="descrição"):
            create_expense({"due_date": "2026-09-10", "amount": 100})

        with pytest.raises(ValueError, match="vencimento"):
            create_expense({"description": "Luz", "amount": 100})

        with pytest.raises(ValueError, match="negativo"):
            create_expense({"description": "Luz", "due_date": "2026-09-10", "amount": -50})

    def test_create_expense_success(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.insert.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{
                "id": "new-exp-123",
                "description": "Supermercado",
                "amount": 450.50,
                "due_date": "2026-09-20",
                "month_ref": "2026-09-01",
                "status": "pendente",
            }]
        )

        item = create_expense(
            {
                "description": "Supermercado",
                "amount": 450.50,
                "due_date": "2026-09-20",
                "month_ref": "2026-09",
            },
            client=mock_client,
        )
        assert item["id"] == "new-exp-123"
        inserted_payload = mock_query.insert.call_args[0][0]
        assert inserted_payload["month_ref"] == "2026-09-01"
        assert inserted_payload["description"] == "Supermercado"

    def test_update_expense(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{"id": "exp-1", "amount": 500.0}]
        )

        res = update_expense("exp-1", {"amount": 500.0}, client=mock_client)
        assert res["amount"] == 500.0
        mock_query.eq.assert_called_with("id", "exp-1")

    def test_delete_expense(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{"id": "exp-1"}])

        assert delete_expense("exp-1", client=mock_client)

    def test_delete_expenses_batch(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.delete.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{"id": "exp-1"}, {"id": "exp-2"}])

        assert delete_expenses_batch(["exp-1", "exp-2"], client=mock_client)
        mock_client.table.assert_called_with("expenses")
        mock_query.delete.assert_called_once()
        mock_query.in_.assert_called_once_with("id", ["exp-1", "exp-2"])

    def test_delete_expenses_batch_empty(self):
        assert delete_expenses_batch([]) is True


class TestToggleExpenseStatus:
    """AC-009: Marcar despesa como paga preenche payment_date e vice-versa."""

    def test_toggle_pendente_to_pago_fills_payment_date(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.select.return_value = mock_query

        today_str = datetime.now().strftime("%Y-%m-%d")
        mock_query.execute.return_value = MagicMock(
            data=[{
                "id": "exp-1",
                "status": "pago",
                "payment_date": today_str,
            }]
        )

        res = toggle_expense_status("exp-1", current_status="pendente", client=mock_client)
        assert res["status"] == "pago"
        assert res["payment_date"] == today_str

        # Verifica payload passado para update
        payload = mock_query.update.call_args[0][0]
        assert payload["status"] == "pago"
        assert payload["payment_date"] == today_str

    def test_toggle_pago_to_pendente_clears_payment_date(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{
                "id": "exp-1",
                "status": "pendente",
                "payment_date": None,
            }]
        )

        res = toggle_expense_status("exp-1", current_status="pago", client=mock_client)
        assert res["status"] == "pendente"
        assert res["payment_date"] is None

        payload = mock_query.update.call_args[0][0]
        assert payload["status"] == "pendente"
        assert payload["payment_date"] is None


class TestPreviousMonthPending:
    """Validação da consulta de pendências do mês anterior para alerta com badge."""

    def test_get_previous_month_ref(self):
        from services.expenses import get_previous_month_ref
        assert get_previous_month_ref("2026-09") == "2026-08"
        assert get_previous_month_ref("2026-01") == "2025-12"
        assert get_previous_month_ref("2026-03-01") == "2026-02"

    def test_get_previous_month_pending_with_items(self):
        from services.expenses import get_previous_month_pending
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {"id": "exp-prev-1", "description": "Luz", "amount": 150.0, "status": "pendente"},
                {"id": "exp-prev-2", "description": "Internet", "amount": 100.0, "status": "pendente"},
            ]
        )

        res = get_previous_month_pending("2026-09", client=mock_client)
        assert res["prev_month_ref"] == "2026-08"
        assert res["count"] == 2
        assert res["total_amount"] == 250.0
        assert len(res["items"]) == 2

