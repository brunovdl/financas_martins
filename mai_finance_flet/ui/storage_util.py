"""
storage_util.py — Persistência local por sessão do MAI Finance (Flet 1.x).

- Os valores da sessão ficam em memória em `page._mai_storage` (um dicionário por página/aba).
- Web: persiste no navegador de cada pessoa via `ft.SharedPreferences` (localStorage).
  Nunca grava em disco no servidor, pois o arquivo seria compartilhado entre todos os visitantes.
- Nativo (Android/Desktop): persiste em cache JSON no diretório de dados do app (um único usuário por dispositivo).
"""
from __future__ import annotations

import json
import os
from typing import Any
import flet as ft

# Chaves restauradas do armazenamento persistente ao abrir o app
PERSISTED_KEYS = (
    "auth_token",
    "user",
    "user_data",
    "remember_login",
    "saved_email",
    "theme_mode",
    "mai_finance_hide_values",
    "shopping_city",
    "shopping_market",
)

# Chaves que versões antigas gravavam e não devem mais existir (ex.: senha em texto puro)
LEGACY_KEYS = ("saved_password",)


def _get_cache_dir() -> str:
    """Retorna o diretório persistente adequado para a plataforma (Android / Desktop)."""
    # 1. Variável oficial do Flet no Android (Serious Python aponta para dados do app)
    flet_storage = os.environ.get("FLET_APP_STORAGE_DATA")
    if flet_storage and os.path.isdir(flet_storage):
        target = os.path.join(flet_storage, ".mai_finance")
        try:
            os.makedirs(target, exist_ok=True)
            return target
        except Exception:
            pass

    # 2. Caminhos do sandbox Android
    for p in (
        os.environ.get("ANDROID_DATA"),
        "/data/data/com.martinsautomation.mai_finance/files",
        "/data/user/0/com.martinsautomation.mai_finance/files",
    ):
        if p and os.path.isdir(p):
            target = os.path.join(p, ".mai_finance")
            try:
                os.makedirs(target, exist_ok=True)
                return target
            except Exception:
                pass

    # 3. Diretório home do usuário (Desktop)
    try:
        home = os.path.expanduser("~")
        if home and home != "/" and os.path.isdir(home):
            target = os.path.join(home, ".mai_finance")
            os.makedirs(target, exist_ok=True)
            return target
    except Exception:
        pass

    # 4. Fallback relativo ao app
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mai_cache")
    try:
        os.makedirs(local, exist_ok=True)
        return local
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))


def _get_cache_file() -> str:
    return os.path.join(_get_cache_dir(), "session_cache.json")


def _legacy_cache_files() -> list[str]:
    return [
        _get_cache_file(),
        os.path.join(os.path.expanduser("~"), ".mai_finance", "session_cache.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mai_session_cache.json"),
    ]


def _read_disk_cache() -> dict[str, Any]:
    # Tenta ler do diretório dinâmico prioritário e fallbacks legados
    for path in _legacy_cache_files():
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
        cache_file = _get_cache_file()
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        tmp_file = f"{cache_file}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, cache_file)
    except Exception as exc:
        print(f"[storage_util] Erro ao gravar cache em disco: {exc}")


def _delete_disk_caches() -> None:
    for path in _legacy_cache_files():
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _is_testing(page: Any) -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ or "Mock" in type(page).__name__


def _is_web(page: Any) -> bool:
    return getattr(page, "web", False) is True


def _uses_disk_cache(page: Any) -> bool:
    """Cache em disco apenas no app nativo (fora de testes). Na web o disco é do servidor."""
    return not _is_web(page) and not _is_testing(page)


def _memory(page: Any) -> dict[str, Any]:
    store = getattr(page, "_mai_storage", None)
    if not isinstance(store, dict):
        store = {}
        page._mai_storage = store
    return store


def _decode(val: Any) -> Any:
    if isinstance(val, (dict, list, int, float, bool)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return val


async def load_local_storage(page: ft.Page) -> None:
    """
    Carrega os valores persistidos para a memória da sessão. Chamar uma vez ao abrir o app.
    Também remove dados legados (senha salva e, na web, o cache em disco do servidor).
    """
    store = _memory(page)

    if _is_web(page):
        _delete_disk_caches()
        try:
            prefs = ft.SharedPreferences()
            page._mai_prefs = prefs
            for key in LEGACY_KEYS:
                await prefs.remove(key)
            for key in PERSISTED_KEYS:
                val = await prefs.get(key)
                if isinstance(val, str):
                    store[key] = val
        except Exception as exc:
            print(f"[storage_util] Erro ao carregar armazenamento do navegador: {exc}")
        return

    if _uses_disk_cache(page):
        cache = _read_disk_cache()
        if any(key in cache for key in LEGACY_KEYS):
            for key in LEGACY_KEYS:
                cache.pop(key, None)
            _write_disk_cache(cache)
        for key in PERSISTED_KEYS:
            if key in cache:
                store[key] = cache[key]


def _persist_browser(page: Any, method: str, *args: Any) -> None:
    """Agenda a gravação no navegador sem bloquear o handler atual."""
    prefs = getattr(page, "_mai_prefs", None)
    if prefs is None:
        return
    try:
        page.run_task(getattr(prefs, method), *args)
    except Exception as exc:
        print(f"[storage_util] Erro ao gravar no navegador: {exc}")


def set_local_items(page: ft.Page, items: dict[str, Any]) -> None:
    """Salva múltiplos itens na sessão e no armazenamento persistente da plataforma."""
    store = _memory(page)
    for key, value in items.items():
        val_str = json.dumps(value) if not isinstance(value, str) else value
        store[key] = val_str
        _persist_browser(page, "set", key, val_str)

    if _uses_disk_cache(page):
        cache = _read_disk_cache()
        for key in items:
            cache[key] = store[key]
        _write_disk_cache(cache)


def set_local_item(page: ft.Page, key: str, value: Any) -> None:
    """Salva um item na sessão e no armazenamento persistente da plataforma."""
    set_local_items(page, {key: value})


def get_local_item(page: ft.Page, key: str) -> Any | None:
    """Recupera um item da sessão (já carregada do armazenamento persistente)."""
    val = _memory(page).get(key)
    if val is None:
        return None
    return _decode(val)


def remove_local_item(page: ft.Page, key: str) -> None:
    """Remove um item da sessão e do armazenamento persistente da plataforma."""
    _memory(page).pop(key, None)
    _persist_browser(page, "remove", key)

    if _uses_disk_cache(page):
        cache = _read_disk_cache()
        if key in cache:
            del cache[key]
            _write_disk_cache(cache)
