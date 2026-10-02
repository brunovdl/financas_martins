"""
test_security_fixes.py — Regressões das correções de segurança:
- Sessões do modo web nunca passam pelo disco do servidor (isolamento entre navegadores)
- "Lembrar de mim" usa token de longa duração em vez da senha em texto puro
- JWT_SECRET nunca hard-coded (ambiente ou segredo local persistido)
"""
from __future__ import annotations

import importlib
import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-32-bytes-long!")

import db.auth as auth_util
from services.auth_service import refresh_session_with_remember_token
from ui import storage_util
from ui.storage_util import get_local_item, preload_local_items, remove_local_item, set_local_items


class FakeAsyncPrefs:
    """Imita o SharedPreferences do Flet 1.0 (métodos assíncronos) — no web é o localStorage."""

    def __init__(self) -> None:
        self.data: dict[str, object] = {}

    async def set(self, key, value):
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def remove(self, key):
        self.data.pop(key, None)
        return True


class FakePage:
    def __init__(self, web: bool, prefs: FakeAsyncPrefs | None = None) -> None:
        self.web = web
        self.session = None
        self.shared_preferences = prefs
        self.tasks: list = []

    def run_task(self, handler, *args):
        self.tasks.append(handler(*args))

    async def flush(self) -> None:
        while self.tasks:
            await self.tasks.pop(0)


@pytest.fixture
def disk_cache(tmp_path, monkeypatch):
    """Habilita o cache em disco (desligado em testes) apontando para um arquivo temporário."""
    cache_file = tmp_path / "session_cache.json"
    monkeypatch.setattr(storage_util, "_get_cache_file", lambda: str(cache_file))
    monkeypatch.setattr(storage_util, "_is_testing", lambda page: False)
    monkeypatch.setattr(
        storage_util, "_read_disk_cache",
        lambda: json.loads(cache_file.read_text()) if cache_file.exists() else {},
    )
    return cache_file


class TestWebSessionIsolation:
    def test_native_app_persists_session_on_device_disk(self, disk_cache):
        set_local_items(FakePage(web=False), {"auth_token": "tok-celular"})
        assert get_local_item(FakePage(web=False), "auth_token") == "tok-celular"

    async def test_web_never_writes_session_to_server_disk(self, disk_cache):
        page = FakePage(web=True, prefs=FakeAsyncPrefs())
        set_local_items(page, {"auth_token": "tok-web"})
        await page.flush()
        assert not disk_cache.exists()

    def test_web_never_reads_another_users_session_from_server_disk(self, disk_cache):
        disk_cache.write_text(json.dumps({"auth_token": "tok-de-outra-pessoa"}))
        assert get_local_item(FakePage(web=True, prefs=FakeAsyncPrefs()), "auth_token") is None

    async def test_web_logout_does_not_touch_server_disk(self, disk_cache):
        disk_cache.write_text(json.dumps({"auth_token": "tok-celular"}))
        page = FakePage(web=True, prefs=FakeAsyncPrefs())
        remove_local_item(page, "auth_token")
        await page.flush()
        assert json.loads(disk_cache.read_text()) == {"auth_token": "tok-celular"}

    async def test_web_persists_in_browser_storage_and_preloads_next_session(self):
        browser = FakeAsyncPrefs()
        first = FakePage(web=True, prefs=browser)
        set_local_items(first, {"auth_token": "tok-web", "remember_login": True})
        await first.flush()
        assert browser.data["auth_token"] == "tok-web"

        # Recarregar a aba: nova sessão Python, mesmo navegador
        reloaded = FakePage(web=True, prefs=browser)
        assert get_local_item(reloaded, "auth_token") is None  # leitura assíncrona exige preload
        await preload_local_items(reloaded, ["auth_token", "remember_login"])
        assert get_local_item(reloaded, "auth_token") == "tok-web"
        assert get_local_item(reloaded, "remember_login") is True

        # Outro navegador não enxerga nada
        other = FakePage(web=True, prefs=FakeAsyncPrefs())
        await preload_local_items(other, ["auth_token"])
        assert get_local_item(other, "auth_token") is None

    async def test_web_remove_clears_browser_storage(self):
        browser = FakeAsyncPrefs()
        page = FakePage(web=True, prefs=browser)
        set_local_items(page, {"auth_token": "tok-web"})
        remove_local_item(page, "auth_token")
        await page.flush()
        assert "auth_token" not in browser.data
        assert get_local_item(page, "auth_token") is None


class TestRememberToken:
    def test_remember_token_is_not_a_session(self):
        token = auth_util.create_remember_token("u1", "Bruno", "b@x.com")
        assert auth_util.verify_remember_token(token)["userId"] == "u1"
        assert auth_util.verify_token(token) is None

    def test_session_token_is_not_a_remember_token(self):
        token = auth_util.create_token("u1", "Bruno", "b@x.com")
        assert auth_util.verify_token(token) is not None
        assert auth_util.verify_remember_token(token) is None

    def test_remember_token_lasts_longer_than_session(self):
        token = auth_util.create_remember_token("u1", "Bruno", "b@x.com")
        payload = auth_util.verify_remember_token(token)
        assert payload["exp"] - payload["iat"] == auth_util.config.REMEMBER_DURATION_SECONDS
        assert auth_util.config.REMEMBER_DURATION_SECONDS > auth_util.config.SESSION_DURATION_SECONDS

    def test_tampered_remember_token_rejected(self):
        token = auth_util.create_remember_token("u1", "Bruno", "b@x.com")
        header, payload, sig = token.split(".")
        forged = auth_util._b64url_encode(json.dumps({"userId": "admin", "purpose": "remember", "exp": 9999999999}))
        assert auth_util.verify_remember_token(f"{header}.{forged}.{sig}") is None


def _client_returning(rows):
    client = MagicMock()
    query = client.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.limit.return_value = query
    query.execute.return_value = MagicMock(data=rows)
    return client


class TestRefreshSession:
    def test_valid_remember_token_issues_new_session(self):
        remember = auth_util.create_remember_token("u1", "Bruno", "b@x.com")
        client = _client_returning([{"id": "u1", "name": "Bruno", "email": "b@x.com"}])

        ok, result = refresh_session_with_remember_token(remember, client=client)

        assert ok is True
        assert auth_util.verify_token(result["token"])["userId"] == "u1"
        assert auth_util.verify_remember_token(result["remember_token"])["userId"] == "u1"
        assert result["user"] == {"id": "u1", "name": "Bruno", "email": "b@x.com"}
        client.table.return_value.eq.assert_called_with("id", "u1")

    def test_invalid_token_rejected_without_querying_db(self):
        client = MagicMock()
        ok, _ = refresh_session_with_remember_token("lixo", client=client)
        assert ok is False
        client.table.assert_not_called()

    def test_session_token_cannot_be_used_to_refresh(self):
        session = auth_util.create_token("u1", "Bruno", "b@x.com")
        ok, _ = refresh_session_with_remember_token(session, client=MagicMock())
        assert ok is False

    def test_deleted_user_cannot_refresh(self):
        remember = auth_util.create_remember_token("u1", "Bruno", "b@x.com")
        ok, _ = refresh_session_with_remember_token(remember, client=_client_returning([]))
        assert ok is False


class TestJwtSecret:
    def test_jwt_secret_from_environment(self):
        import config
        with patch.dict(os.environ, {"JWT_SECRET": "segredo-do-ambiente"}):
            importlib.reload(config)
            assert config.JWT_SECRET == "segredo-do-ambiente"
        importlib.reload(config)

    def test_jwt_secret_generated_once_and_persisted(self, tmp_path):
        import config
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(config, "_local_data_dirs", return_value=[tmp_path / "dados"]):
                first = config._load_or_create_local_secret()
                second = config._load_or_create_local_secret()
        assert first == second
        assert len(first) >= 32
        assert (tmp_path / "dados" / "jwt_secret").read_text() == first

    def test_no_hardcoded_jwt_secret_in_source(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parent.parent / "config.py").read_text(encoding="utf-8")
        assert "mai-finance-secure-jwt-secret-key" not in source
