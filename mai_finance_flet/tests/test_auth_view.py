"""
test_auth_view.py — Testes unitários para AuthView (Flet).
Valida login sem cadastro, validações inline e interação com sessão local.
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
    page._mai_storage = {}
    page.update = MagicMock()
    return page


class TestAuthView:
    def test_initial_state_is_login(self, mock_page):
        view = AuthView(mock_page)
        assert view.email_field.visible
        assert view.password_field.visible
        assert not view.error_box.visible

    def test_signup_is_disabled(self, mock_page):
        view = AuthView(mock_page)
        assert not hasattr(view, "name_field")
        assert not hasattr(view, "tab_register_btn")
        assert view.submit_btn_text.value == "Acessar Conta"

    def test_notice_is_shown_on_open(self, mock_page):
        view = AuthView(mock_page, notice="Sua sessão de 24 horas expirou.")
        assert view.error_box.visible
        assert "expirou" in view.error_text.value

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
    def test_remember_saves_only_email(self, mock_login, mock_page):
        mock_login.return_value = (True, {"token": "tok123", "user": {"name": "Bruno"}})
        view = AuthView(mock_page)
        view.email_field.value = "lembrar@exemplo.com"
        view.password_field.value = "segredo123"
        view.remember_checkbox.value = True

        view._handle_submit(None)

        assert get_local_item(mock_page, "saved_email") == "lembrar@exemplo.com"
        assert get_local_item(mock_page, "saved_password") is None
        assert "segredo123" not in str(mock_page._mai_storage)

        # Novo AuthView inicializa só com o e-mail preenchido
        new_view = AuthView(mock_page)
        assert new_view.email_field.value == "lembrar@exemplo.com"
        assert not new_view.password_field.value
        assert new_view.remember_checkbox.value is True

    @patch("ui.auth_view.login_user")
    def test_unchecked_remember_forgets_email(self, mock_login, mock_page):
        mock_login.return_value = (True, {"token": "tok123", "user": {"name": "Bruno"}})
        view = AuthView(mock_page)
        view.email_field.value = "lembrar@exemplo.com"
        view.password_field.value = "segredo123"
        view.remember_checkbox.value = False
        view._handle_submit(None)

        assert get_local_item(mock_page, "saved_email") is None
