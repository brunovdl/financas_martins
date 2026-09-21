"""
shopping_realtime.py — Sincronização em tempo real da lista de compras (T-018).

Implementa:
- Monitoramento ativo de alterações na tabela shopping_items (AC-027)
- Notificação imediata para a interface quando o parceiro(a) adiciona ou marca 'OK'
- Modo adaptativo de alta frequência para quando o usuário está no mercado (3s)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
from typing import Any, Callable
from db.shopping import list_shopping_items

logger = logging.getLogger(__name__)


def compute_items_signature(items: list[dict[str, Any]]) -> str:
    """Calcula hash determinístico do estado dos itens para detectar mutações em tempo real."""
    simplified = [
        {
            "id": it.get("id"),
            "name": it.get("name"),
            "qty": it.get("quantity"),
            "bought": it.get("is_bought"),
            "act_price": it.get("actual_price"),
            "updated_at": it.get("updated_at"),
        }
        for it in sorted(items, key=lambda x: str(x.get("id", "")))
    ]
    raw = json.dumps(simplified, sort_keys=True, default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


class ShoppingRealtimeSync:
    """
    Gerencia a escuta reativa da lista de compras para sincronização instantânea
    entre os celulares de Bruno e sua esposa no mercado (AC-027).
    """

    def __init__(
        self,
        on_change_callback: Callable[[list[dict[str, Any]]], None],
        interval_seconds: float = 3.0,
    ) -> None:
        self.on_change_callback = on_change_callback
        self.interval = interval_seconds
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_signature = ""

    def start(self) -> None:
        """Inicia o monitoramento em segundo plano."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Encerra a sincronização reativa."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def trigger_local_update(self, items: list[dict[str, Any]]) -> None:
        """Atualiza a assinatura local para evitar re-notificações redundantes."""
        self._last_signature = compute_items_signature(items)

    def _run_loop(self) -> None:
        while self._running:
            try:
                current_items = list_shopping_items()
                sig = compute_items_signature(current_items)
                if self._last_signature and sig != self._last_signature:
                    self._last_signature = sig
                    try:
                        self.on_change_callback(current_items)
                    except Exception as cb_exc:
                        logger.error(f"Erro no callback de realtime da lista de compras: {cb_exc}")
                elif not self._last_signature:
                    self._last_signature = sig
            except Exception as exc:
                err_msg = str(exc)
                if "[WinError 10035]" not in err_msg and "WSAEWOULDBLOCK" not in err_msg:
                    logger.warning(f"Erro ao verificar atualização realtime: {exc}")
                else:
                    logger.debug(f"I/O transitório do Windows em realtime: {exc}")

            import time
            time.sleep(self.interval)
