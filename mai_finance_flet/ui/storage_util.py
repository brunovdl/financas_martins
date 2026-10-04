"""
storage_util.py — Utilitário de persistência local compatível com Flet 0.x e 1.x.

Gerencia armazenamento local para tokens, credenciais salvas e dados de sessão
abstraindo diferenças entre shared_preferences, session, client_storage e cache em disco.
"""
from __future__ import annotations

import inspect
import json
import os
from typing import Any
import flet as ft

def _get_cache_dir() -> str:
    """Retorna o diretório persistente adequado para a plataforma (Android / Desktop / Web)."""
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


def _read_disk_cache() -> dict[str, Any]:
    # Tenta ler do diretório dinâmico prioritário e fallbacks legados
    current_file = _get_cache_file()
    legacy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mai_session_cache.json")
    old_home_file = os.path.join(os.path.expanduser("~"), ".mai_finance", "session_cache.json")

    for path in (current_file, old_home_file, legacy_file):
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


def _is_web(page: ft.Page) -> bool:
    """True quando a página roda no navegador (Flet Web): o Python executa no servidor."""
    return getattr(page, "web", False) is True


def _is_testing(page: ft.Page) -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ or "Mock" in type(page).__name__


def _use_disk_cache(page: ft.Page) -> bool:
    """
    O cache em disco só é seguro em app nativo (Android/Desktop), onde o disco é do
    próprio usuário. No modo web o disco é do SERVIDOR e seria compartilhado entre
    todos os navegadores conectados — por isso nunca é usado lá.
    """
    return not _is_web(page) and not _is_testing(page)


def _get_prefs(page: ft.Page) -> Any | None:
    """Retorna o armazenamento persistente do cliente (no web: localStorage do navegador)."""
    prefs = getattr(page, "shared_preferences", None)
    if prefs:
        return prefs
    if _is_web(page):
        prefs = getattr(page, "_mai_prefs", None)
        if prefs is None:
            try:
                prefs = ft.SharedPreferences()
                page._mai_prefs = prefs
            except Exception as exc:
                print(f"[storage_util] SharedPreferences indisponível: {exc}")
                return None
        return prefs
    return None


def _run_in_background(page: ft.Page, awaitable: Any) -> None:
    """Agenda uma chamada assíncrona (ex.: SharedPreferences do Flet 1.0) sem bloquear a UI."""
    async def _runner() -> None:
        try:
            await awaitable
        except Exception as exc:
            print(f"[storage_util] Falha ao persistir no cliente: {exc}")

    run_task = getattr(page, "run_task", None)
    try:
        if callable(run_task):
            run_task(_runner)
            return
    except Exception:
        pass
    if hasattr(awaitable, "close"):
        awaitable.close()


def _call_store(page: ft.Page, store: Any, method: str, *args: Any) -> Any:
    """Chama um método de armazenamento síncrono ou assíncrono, sem nunca lançar exceção."""
    if not store:
        return None
    try:
        result = getattr(store, method)(*args)
    except Exception:
        return None
    if inspect.isawaitable(result):
        if method == "get":
            # Leitura assíncrona não cabe numa chamada síncrona; use preload_local_items
            if hasattr(result, "close"):
                result.close()
            return None
        _run_in_background(page, result)
        return None
    return result


def _storage_sources(page: ft.Page) -> list[Any]:
    return [
        _get_prefs(page),
        getattr(page, "session", None),
        getattr(page, "client_storage", None),
    ]


def _decode(val: Any) -> Any:
    if isinstance(val, (dict, list, int, float, bool)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return val


def _page_memory(page: ft.Page) -> dict[str, Any]:
    if not isinstance(getattr(page, "_mai_storage", None), dict):
        page._mai_storage = {}
    return page._mai_storage


async def preload_local_items(page: ft.Page, keys: list[str]) -> None:
    """
    Carrega para a memória da sessão os valores salvos no cliente (no web, o
    localStorage do navegador), cuja leitura no Flet 1.0 é assíncrona.
    Deve ser aguardado antes de get_local_item no início da sessão web.
    """
    prefs = _get_prefs(page)
    if prefs is None:
        return
    memory = _page_memory(page)
    for key in keys:
        try:
            res = prefs.get(key)
            if inspect.isawaitable(res):
                res = await res
        except Exception:
            continue
        if _is_valid_storage_val(res):
            memory[key] = res


def purge_disk_cache() -> None:
    """Apaga o cache de sessão em disco (usado no servidor web para remover dados legados)."""
    legacy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mai_session_cache.json")
    for path in (_get_cache_file(), legacy_file):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as exc:
            print(f"[storage_util] Não foi possível remover {path}: {exc}")


def set_local_items(page: ft.Page, items: dict[str, Any]) -> None:
    """Salva múltiplos itens em lote na sessão e no armazenamento persistente do cliente."""
    use_disk = _use_disk_cache(page)
    cache = _read_disk_cache() if use_disk else {}
    memory = _page_memory(page)
    sources = _storage_sources(page)

    for key, value in items.items():
        val_str = json.dumps(value) if not isinstance(value, str) else value
        cache[key] = val_str
        memory[key] = val_str
        for store in sources:
            _call_store(page, store, "set", key, val_str)

    if use_disk:
        _write_disk_cache(cache)


def set_local_item(page: ft.Page, key: str, value: Any) -> None:
    """Salva um item na sessão/armazenamento da página e em cache persistente."""
    set_local_items(page, {key: value})


def _is_valid_storage_val(val: Any) -> bool:
    if val is None:
        return False
    if "Mock" in type(val).__name__:
        return False
    return isinstance(val, (str, dict, list, int, float, bool))


def get_local_item(page: ft.Page, key: str) -> Any | None:
    """Recupera um item da memória da sessão, do armazenamento do cliente ou (nativo) do disco."""
    val = None

    memory = getattr(page, "_mai_storage", None)
    if isinstance(memory, dict) and _is_valid_storage_val(memory.get(key)):
        val = memory[key]

    if val is None:
        for store in _storage_sources(page):
            res = _call_store(page, store, "get", key)
            if _is_valid_storage_val(res):
                val = res
                break

    if val is None and _use_disk_cache(page):
        val = _read_disk_cache().get(key)

    if val is None:
        return None
    return _decode(val)


def remove_local_item(page: ft.Page, key: str) -> None:
    """Remove um item da sessão/armazenamento da página e do cache persistente."""
    if not _is_web(page):
        cache = _read_disk_cache()
        if key in cache:
            del cache[key]
            _write_disk_cache(cache)

    for store in _storage_sources(page):
        _call_store(page, store, "remove", key)

    memory = getattr(page, "_mai_storage", None)
    if isinstance(memory, dict):
        memory.pop(key, None)
