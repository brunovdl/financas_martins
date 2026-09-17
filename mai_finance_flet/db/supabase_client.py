"""
supabase_client.py — Cliente Supabase singleton para o MAI Finance Flet.

Usa Anon Key (igual ao Next.js atual — sem Supabase Auth nativo).
O RLS é respeitado pelas policies existentes no banco.

Também fornece um helper de polling de 30s como substituto do Realtime.
"""
from __future__ import annotations

import asyncio
from typing import Callable

from supabase import create_client, Client

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

_client: Client | None = None


def get_client() -> Client:
    """Retorna o cliente Supabase singleton (Anon Key)."""
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
    return _client


# ---------------------------------------------------------------------------
# Polling helper — substituto do Supabase Realtime
# ---------------------------------------------------------------------------

class PollingSubscription:
    """
    Simula o comportamento de uma subscription Realtime usando polling de 30s.

    Uso:
        sub = PollingSubscription(fetch_fn=lambda: client.table(...).select(...).execute().data,
                                  callback=on_update)
        await sub.start()
        ...
        sub.stop()
    """

    INTERVAL: int = 30  # segundos

    def __init__(self, fetch_fn: Callable, callback: Callable, interval: int = INTERVAL) -> None:
        self._fetch = fetch_fn
        self._callback = callback
        self._interval = interval
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Inicia o loop de polling em background."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        """Para o loop de polling."""
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while self._running:
            try:
                data = self._fetch()
                self._callback(data)
            except Exception as exc:  # noqa: BLE001
                print(f"[PollingSubscription] erro no polling: {exc}")
            await asyncio.sleep(self._interval)
