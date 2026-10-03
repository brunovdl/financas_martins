"""
test_session_storage.py — Sessão de 24h e armazenamento por navegador (Fase 1 de segurança).
"""
from __future__ import annotations

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

import app
from db.auth import create_token
from ui.storage_util import get_local_item, load_local_storage, remove_local_item, set_local_item


def _expired_token() -> str:
    with patch("db.auth.time.time", return_value=time.time() - 90_000):
        return create_token("1", "Bruno", "bruno@exemplo.com")


def _web_page(prefs_data: dict) -> MagicMock:
    page = MagicMock()
    page.web = True
    page._mai_storage = None
    prefs = MagicMock()
    prefs.get = AsyncMock(side_effect=lambda k: prefs_data.get(k))
    prefs.remove = AsyncMock()
    return page, prefs


class TestBrowserStorage:
    def test_web_loads_from_browser_and_never_reads_server_disk(self):
        page, prefs = _web_page({"auth_token": "tok-do-navegador", "saved_email": "a@b.com"})
        with patch("ui.storage_util.ft.SharedPreferences", return_value=prefs), \
             patch("ui.storage_util._read_disk_cache") as read_disk, \
             patch("ui.storage_util._delete_disk_caches") as delete_disk:
            asyncio.run(load_local_storage(page))

        read_disk.assert_not_called()
        delete_disk.assert_called_once()
        assert get_local_item(page, "auth_token") == "tok-do-navegador"
        assert get_local_item(page, "saved_email") == "a@b.com"

    def test_web_removes_legacy_saved_password(self):
        page, prefs = _web_page({"saved_password": "segredo"})
        with patch("ui.storage_util.ft.SharedPreferences", return_value=prefs), \
             patch("ui.storage_util._delete_disk_caches"):
            asyncio.run(load_local_storage(page))

        prefs.remove.assert_any_await("saved_password")
        assert get_local_item(page, "saved_password") is None

    def test_two_web_pages_do_not_share_session(self):
        page_a, prefs_a = _web_page({"auth_token": "tok-bruno"})
        page_b, prefs_b = _web_page({})
        with patch("ui.storage_util._delete_disk_caches"):
            with patch("ui.storage_util.ft.SharedPreferences", return_value=prefs_a):
                asyncio.run(load_local_storage(page_a))
            with patch("ui.storage_util.ft.SharedPreferences", return_value=prefs_b):
                asyncio.run(load_local_storage(page_b))

        assert get_local_item(page_a, "auth_token") == "tok-bruno"
        assert get_local_item(page_b, "auth_token") is None

    def test_web_writes_go_to_browser_not_disk(self):
        page, prefs = _web_page({})
        page._mai_prefs = prefs
        with patch("ui.storage_util._write_disk_cache") as write_disk:
            set_local_item(page, "auth_token", "novo")
            remove_local_item(page, "saved_email")

        write_disk.assert_not_called()
        methods = [c.args[0] for c in page.run_task.call_args_list]
        assert prefs.set in methods and prefs.remove in methods

    def test_native_purges_legacy_password_from_disk(self):
        page = MagicMock()
        page.web = False
        page._mai_storage = None
        cache = {"auth_token": "tok", "saved_password": "segredo"}
        with patch("ui.storage_util._uses_disk_cache", return_value=True), \
             patch("ui.storage_util._read_disk_cache", return_value=dict(cache)), \
             patch("ui.storage_util._write_disk_cache") as write_disk:
            asyncio.run(load_local_storage(page))

        written = write_disk.call_args[0][0]
        assert "saved_password" not in written
        assert get_local_item(page, "auth_token") == "tok"


def _run_main(token: str | None):
    page = MagicMock()
    page._mai_storage = {"auth_token": token} if token else {}
    page.pop_dialog.return_value = None
    with patch("app.AuthView") as auth_view, patch("app.DashboardView") as dashboard_view:
        asyncio.run(app.main(page))
    return page, auth_view, dashboard_view


class TestSession24h:
    def test_valid_token_opens_dashboard_and_starts_watch(self):
        page, auth_view, dashboard_view = _run_main(create_token("1", "Bruno", "b@x.com"))
        dashboard_view.assert_called_once()
        auth_view.assert_not_called()
        assert page.run_task.call_args[0][0].__name__ == "_watch_session"

    def test_expired_token_goes_to_login_with_notice(self):
        page, auth_view, dashboard_view = _run_main(_expired_token())
        dashboard_view.assert_not_called()
        assert auth_view.call_args.kwargs["notice"] == app.SESSION_EXPIRED_MESSAGE
        assert get_local_item(page, "auth_token") is None

    def test_no_token_goes_to_login_without_notice(self):
        _, auth_view, dashboard_view = _run_main(None)
        dashboard_view.assert_not_called()
        assert auth_view.call_args.kwargs["notice"] is None

    def test_session_expiring_while_in_use_logs_out_immediately(self):
        page = MagicMock()
        page._mai_storage = {"auth_token": create_token("1", "Bruno", "b@x.com")}
        page.pop_dialog.return_value = None
        with patch("app.AuthView") as auth_view, patch("app.DashboardView"):
            asyncio.run(app.main(page))
            watch, generation = page.run_task.call_args[0]

            # O token vence com o app aberto
            page._mai_storage["auth_token"] = _expired_token()
            asyncio.run(watch(generation))

        assert auth_view.call_args.kwargs["notice"] == app.SESSION_EXPIRED_MESSAGE
        assert get_local_item(page, "auth_token") is None
        page.pop_dialog.assert_called()

    def test_watch_sleeps_until_expiry_then_logs_out(self):
        page = MagicMock()
        page._mai_storage = {"auth_token": create_token("1", "Bruno", "b@x.com")}
        page.pop_dialog.return_value = None
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)
            page._mai_storage["auth_token"] = _expired_token()

        with patch("app.AuthView") as auth_view, patch("app.DashboardView"):
            asyncio.run(app.main(page))
            watch, generation = page.run_task.call_args[0]
            with patch("app.asyncio.sleep", fake_sleep):
                asyncio.run(watch(generation))

        assert sleeps == [app.SESSION_CHECK_INTERVAL_SECONDS]
        assert auth_view.call_args.kwargs["notice"] == app.SESSION_EXPIRED_MESSAGE

