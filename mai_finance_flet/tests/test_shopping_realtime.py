"""
test_shopping_realtime.py — Testes da sincronização em tempo real (T-018).

Cobre os critérios de aceite:
- @spec:AC-027 — Sincronização em tempo real entre celulares via Supabase Realtime
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
import pytest

from services.shopping_realtime import compute_items_signature, ShoppingRealtimeSync


class TestShoppingRealtime:
    """Validação da detecção e sincronização reativa entre aparelhos."""

    def test_signature_changes_on_status_or_price(self):
        items_v1 = [
            {"id": "1", "name": "Leite", "is_bought": False, "quantity": 2, "actual_price": None}
        ]
        items_v2 = [
            {"id": "1", "name": "Leite", "is_bought": True, "quantity": 2, "actual_price": 5.49}
        ]
        sig1 = compute_items_signature(items_v1)
        sig2 = compute_items_signature(items_v2)
        assert sig1 != sig2

    def test_signature_identical_for_same_content(self):
        items = [{"id": "1", "name": "Leite", "is_bought": False, "quantity": 2}]
        sig1 = compute_items_signature(items)
        sig2 = compute_items_signature([{"id": "1", "name": "Leite", "is_bought": False, "quantity": 2}])
        assert sig1 == sig2

    @patch("services.shopping_realtime.list_shopping_items")
    def test_realtime_sync_notifies_callback_on_remote_change(self, mock_list):
        received_updates = []

        def on_change(new_items):
            received_updates.append(new_items)

        # Primeiro estado
        mock_list.return_value = [{"id": "1", "name": "Arroz", "is_bought": False}]
        sync = ShoppingRealtimeSync(on_change_callback=on_change, interval_seconds=0.05)
        sync.start()

        time.sleep(0.1)

        # Parceiro(a) marcou 'OK' no outro celular
        mock_list.return_value = [{"id": "1", "name": "Arroz", "is_bought": True}]

        time.sleep(0.15)
        sync.stop()

        assert len(received_updates) >= 1
        assert received_updates[-1][0]["is_bought"] is True
