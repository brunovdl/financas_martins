"""
storage_util.py — Utilitário de persistência local compatível com Flet 0.x e 1.x.

Gerencia armazenamento local para tokens, credenciais salvas e dados de sessão
abstraindo diferenças entre shared_preferences, session, client_storage e cache em disco.
"""
from __future__ import annotations

import json
import os
from typing import Any
import flet as ft

_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".mai_finance")
_CACHE_FILE = os.path.join(_CACHE_DIR, "session_cache.json")
_LEGACY_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mai_session_cache.json")


def _read_disk_cache() -> dict[str, Any]:
    # Tenta ler do cache principal (fora da pasta monitorada pelo watcher do Flet)
    for path in (_CACHE_FILE, _LEGACY_CACHE_FILE):
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
    return {}


def _write_disk_cache(data: dict[str, Any]) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        tmp_file = f"{_CACHE_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, _CACHE_FILE)
    except Exception as exc:
        print(f"[storage_util] Erro ao gravar cache em disco: {exc}")


def set_local_items(page: ft.Page, items: dict[str, Any]) -> None:
    """Salva múltiplos itens em lote na sessão e em cache persistente de forma atômica."""
    cache = _read_disk_cache()
    if not hasattr(page, "_mai_storage") or not isinstance(page._mai_storage, dict):
        page._mai_storage = {}

    for key, value in items.items():
        val_str = json.dumps(value) if not isinstance(value, str) else value
        cache[key] = val_str
        page._mai_storage[key] = val_str

        if hasattr(page, "shared_preferences") and page.shared_preferences:
            try:
                page.shared_preferences.set(key, val_str)
            except Exception:
                pass

        if hasattr(page, "session") and page.session:
            try:
                page.session.set(key, val_str)
            except Exception:
                pass

        if hasattr(page, "client_storage") and page.client_storage:
            try:
                page.client_storage.set(key, val_str)
            except Exception:
                pass

    _write_disk_cache(cache)


def set_local_item(page: ft.Page, key: str, value: Any) -> None:
    """Salva um item na sessão/armazenamento da página e em cache persistente."""
    set_local_items(page, {key: value})


def get_local_item(page: ft.Page, key: str) -> Any | None:
    """Recupera um item da sessão/armazenamento da página ou cache persistente."""
    val_str = None

    if hasattr(page, "shared_preferences") and page.shared_preferences:
        try:
            val_str = page.shared_preferences.get(key)
        except Exception:
            pass

    if val_str is None and hasattr(page, "session") and page.session:
        try:
            val_str = page.session.get(key)
        except Exception:
            pass

    if val_str is None and hasattr(page, "client_storage") and page.client_storage:
        try:
            val_str = page.client_storage.get(key)
        except Exception:
            pass

    mai_storage = getattr(page, "_mai_storage", None)
    if val_str is None and isinstance(mai_storage, dict):
        val_str = mai_storage.get(key)

    if val_str is None:
        # Fallback no cache em disco local
        cache = _read_disk_cache()
        val_str = cache.get(key)

    if val_str is None:
        return None

    try:
        return json.loads(val_str)
    except Exception:
        return val_str


def remove_local_item(page: ft.Page, key: str) -> None:
    """Remove um item da sessão/armazenamento da página e do cache persistente."""
    cache = _read_disk_cache()
    if key in cache:
        del cache[key]
        _write_disk_cache(cache)

    if hasattr(page, "shared_preferences") and page.shared_preferences:
        try:
            page.shared_preferences.remove(key)
        except Exception:
            pass

    if hasattr(page, "session") and page.session:
        try:
            page.session.remove(key)
        except Exception:
            pass

    if hasattr(page, "client_storage") and page.client_storage:
        try:
            page.client_storage.remove(key)
        except Exception:
            pass

    if hasattr(page, "_mai_storage") and isinstance(page._mai_storage, dict) and key in page._mai_storage:
        del page._mai_storage[key]
