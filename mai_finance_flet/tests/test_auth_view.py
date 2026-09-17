"""
test_auth_view.py — Testes unitários para AuthView (Flet).
Valida alternância de abas, validações inline e interação com sessão local.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest
import flet as ft

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-32-bytes-long!")

from ui.auth_view import AuthView
from ui.storage_util import get_local_item


@pytest.fixture
def mock_page():
    page = MagicMock()
    storage = {}
    pref = MagicMock()
    pref.get.side_effect = lambda k: storage.get(k)
    pref.set.side_effect = lambda k, v: storage.update({k: v})
    pref.remove.side_effect = lambda k: storage.pop(k, None)
    page.shared_preferences = pref
    page.session = None
    page.client_storage = None
    page.update = MagicMock()
    return page


class TestAuthView:
    def test_initial_state_is_login(self, mock_page):
        view = AuthView(mock_page)
        assert view.current_tab == "login"
        assert not view.name_field.visible
        assert view.email_field.visible
        assert view.password_field.visible
        assert not view.error_box.visible

    def test_switch_to_register_tab(self, mock_page):
        view = AuthView(mock_page)
        view._switch_tab("register")
        assert view.current_tab == "register"
        assert view.name_field.visible
        assert view.submit_btn_text.value == "Concluir Cadastro"
        mock_page.update.assert_called()

    def test_switch_back_to_login_tab(self, mock_page):
        view = AuthView(mock_page)
        view._switch_tab("register")
        view._switch_tab("login")
        assert view.current_tab == "login"
        assert not view.name_field.visible
        assert view.submit_btn_text.value == "Acessar Conta"

    def test_validation_invalid_email_shows_error(self, mock_page):
        view = AuthView(mock_page)
        view.email_field.value = "invalido"
        view.password_field.value = "12345678"
        view._handle_submit(MagicMock())

        assert view.error_box.visible
        assert "e-mail válido" in view.error_text.value

    def test_validation_short_password_shows_error(self, mock_page):
        view = AuthView(mock_page)
        view.email_field.value = "user@exemplo.com"
        view.password_field.value = "12345"
        view._handle_submit(MagicMock())

        assert view.error_box.visible
        assert "mínimo 8 caracteres" in view.error_text.value

    def test_validation_empty_name_on_register(self, mock_page):
        view = AuthView(mock_page)
        view._switch_tab("register")
        view.name_field.value = ""
        view.email_field.value = "user@exemplo.com"
        view.password_field.value = "12345678"
        view._handle_submit(MagicMock())

        assert view.error_box.visible
        assert "nome de usuário" in view.error_text.value

    @patch("ui.auth_view.login_user")
    def test_successful_login_stores_token_and_calls_callback(self, mock_login, mock_page):
        mock_login.return_value = (
            True,
            {
                "token": "fake-jwt-token-xyz",
                "user": {"id": "1", "name": "Bruno", "email": "bruno@exemplo.com"},
            },
        )
        callback = MagicMock()
        view = AuthView(mock_page, on_login_success=callback)
        view.email_field.value = "bruno@exemplo.com"
        view.password_field.value = "minhasenha123"

        view._handle_submit(MagicMock())

        token = get_local_item(mock_page, "auth_token")
        assert token == "fake-jwt-token-xyz"
        callback.assert_called_once_with(
            "fake-jwt-token-xyz",
            {"id": "1", "name": "Bruno", "email": "bruno@exemplo.com"},
        )

    @patch("ui.auth_view.login_user")
    def test_enter_key_submits_login(self, mock_login, mock_page):
        mock_login.return_value = (True, {"token": "tok123", "user": {"name": "Bruno"}})
        callback = MagicMock()
        view = AuthView(mock_page, on_login_success=callback)
        view.email_field.value = "bruno@exemplo.com"
        view.password_field.value = "senha12345"

        # Simula envio ao pressionar Enter na senha
        view.password_field.on_submit(None)
        callback.assert_called_once()

    @patch("ui.auth_view.login_user")
    def test_saved_credentials_persistence(self, mock_login, mock_page):
        mock_login.return_value = (True, {"token": "tok123", "user": {"name": "Bruno"}})
        view = AuthView(mock_page)
        view.email_field.value = "lembrar@exemplo.com"
        view.password_field.value = "segredo123"
        view.remember_checkbox.value = True

        view._handle_submit(None)

        # Verifica se salvou
        assert get_local_item(mock_page, "saved_email") == "lembrar@exemplo.com"
        assert get_local_item(mock_page, "saved_password") == "segredo123"

        # Novo AuthView deve inicializar já preenchido
        new_view = AuthView(mock_page)
        assert new_view.email_field.value == "lembrar@exemplo.com"
        assert new_view.password_field.value == "segredo123"
        assert new_view.remember_checkbox.value is True

