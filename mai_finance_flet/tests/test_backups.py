"""
test_backups.py — Testes unitários para o serviço de backups (T-009).

Cobre os critérios de aceite:
- @spec:AC-014 — Criação de backup manual via RPC do Supabase
- @spec:AC-015 — Restauração repovoa categorias e despesas do snapshot
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from services.backups import (
    list_backups,
    create_manual_backup,
    restore_backup,
)


# ---------------------------------------------------------------------------
# AC-014: Criação de backup manual via RPC
# @spec:AC-014
# ---------------------------------------------------------------------------

class TestCreateBackup:
    """@spec:AC-014 — Chamada à stored function create_backup('manual') via RPC."""

    def test_create_manual_backup_calls_rpc(self):
        mock_client = MagicMock()
        mock_rpc = MagicMock()
        mock_client.rpc.return_value = mock_rpc
        mock_rpc.execute.return_value = MagicMock(data="new-backup-uuid-12345")

        backup_id = create_manual_backup(client=mock_client)
        assert backup_id == "new-backup-uuid-12345"

        mock_client.rpc.assert_called_once_with("create_backup", {"backup_type": "manual"})

    def test_list_backups_ordered_by_created_at_desc(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {"id": "b-1", "type": "manual", "categories_count": 5, "expenses_count": 20},
                {"id": "b-2", "type": "automatico", "categories_count": 5, "expenses_count": 18},
            ]
        )

        res = list_backups(client=mock_client)
        assert len(res) == 2
        mock_client.table.assert_called_with("backups")
        mock_query.order.assert_called_with("created_at", desc=True)


# ---------------------------------------------------------------------------
# AC-015: Restauração a partir do snapshot JSONB
# @spec:AC-015
# ---------------------------------------------------------------------------

class TestRestoreBackup:
    """@spec:AC-015 — Restauração repovoa categorias e despesas do JSONB data."""

    def test_restore_backup_not_found_raises_value_error(self):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[])

        with pytest.raises(ValueError, match="não encontrado"):
            restore_backup("inexistente-id", client=mock_client)

    def test_restore_backup_upserts_snapshot_and_removes_only_extras(self):
        mock_client = MagicMock()
        queries = {"backups": MagicMock(), "expenses": MagicMock(), "categories": MagicMock()}
        mock_client.table.side_effect = lambda name: queries.get(name, MagicMock())

        snapshot_data = {
            "categories": [
                {"id": "cat-1", "name": "Aluguel", "color": "#F2B84B"},
                {"id": "cat-2", "name": "Mercado", "color": "#3FD6C4"},
            ],
            "expenses": [
                {
                    "id": "exp-1",
                    "description": "Supermercado",
                    "amount": 500.0,
                    "due_date": "2026-09-10",
                    "category_id": "cat-2",
                    "status": "pago",
                    "payment_date": "2026-09-08",
                    "observation": None,
                    "month_ref": "2026-09-01",
                }
            ],
        }

        backups_q = queries["backups"]
        backups_q.select.return_value = backups_q
        backups_q.eq.return_value = backups_q
        backups_q.limit.return_value = backups_q
        backups_q.execute.return_value = MagicMock(data=[{"id": "backup-123", "data": snapshot_data}])

        # Estado atual: exp-1 (no snapshot) + exp-extra; cat-1 (no snapshot) + cat-extra
        current = {
            "expenses": [{"id": "exp-1"}, {"id": "exp-extra"}],
            "categories": [{"id": "cat-1"}, {"id": "cat-extra"}],
        }
        upserted = {"categories": [{"id": "cat-1"}, {"id": "cat-2"}], "expenses": [{"id": "exp-1"}]}
        for name in ("expenses", "categories"):
            q = queries[name]
            q.select.return_value.execute.return_value = MagicMock(data=current[name])
            q.delete.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
            q.upsert.return_value.execute.return_value = MagicMock(data=upserted[name])

        res = restore_backup("backup-123", client=mock_client)

        assert res["categories_restored"] == 2
        assert res["expenses_restored"] == 1

        # Só remove o que não está no snapshot — nunca limpa a tabela inteira
        queries["expenses"].delete.return_value.in_.assert_called_once_with("id", ["exp-extra"])
        queries["categories"].delete.return_value.in_.assert_called_once_with("id", ["cat-extra"])
        queries["expenses"].delete.return_value.neq.assert_not_called()
        queries["categories"].delete.return_value.neq.assert_not_called()

        cat_upserted, cat_kwargs = queries["categories"].upsert.call_args
        assert [c["id"] for c in cat_upserted[0]] == ["cat-1", "cat-2"]
        assert cat_upserted[0][0]["color"] == "#F2B84B"
        assert cat_kwargs["on_conflict"] == "id"

        exp_upserted, exp_kwargs = queries["expenses"].upsert.call_args
        assert exp_upserted[0][0]["description"] == "Supermercado"
        assert exp_kwargs["on_conflict"] == "id"
