"""
test_auth_service.py — Testes unitários para as regras de negócio de autenticação.
Cobre: AC-001, AC-002, AC-003, AC-004.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-32-bytes-long!")

import db.auth as auth_util
from services.auth_service import login_user


class TestAuthServiceValidation:
    """Testa validações de entrada sem consultar banco."""

    def test_login_invalid_email(self):
        ok, msg = login_user("emailinvalido", "senha1234")
        assert not ok
        assert "e-mail válido" in msg

    def test_login_short_password(self):
        ok, msg = login_user("user@example.com", "123")
        assert not ok
        assert "mínimo 8 caracteres" in msg


class TestLoginUser:
    """Testa o fluxo de login com mock do Supabase (AC-001, AC-002, AC-003)."""

    def test_user_not_found(self):
        """AC-003: e-mail não cadastrado retorna 'E-mail ou senha incorretos.'"""
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        # Retorna lista vazia
        mock_query.execute.return_value = MagicMock(data=[])

        ok, msg = login_user("naoexiste@exemplo.com", "senha1234", client=mock_client)
        assert not ok
        assert msg == "E-mail ou senha incorretos."

    def test_incorrect_password(self):
        """AC-002: senha incorreta retorna 'E-mail ou senha incorretos.'"""
        real_hash = auth_util.hash_password("senhaCorreta123")

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Bruno",
                "email": "bruno@exemplo.com",
                "password_hash": real_hash,
            }]
        )

        ok, msg = login_user("bruno@exemplo.com", "senhaErrada123", client=mock_client)
        assert not ok
        assert msg == "E-mail ou senha incorretos."

    def test_login_success(self):
        """AC-001: credenciais válidas geram token JWT com 24h e dados do usuário."""
        password = "minhaSenhaSegura123"
        real_hash = auth_util.hash_password(password)

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Bruno",
                "email": "bruno@exemplo.com",
                "password_hash": real_hash,
            }]
        )

        ok, result = login_user("bruno@exemplo.com", password, client=mock_client)
        assert ok
        assert isinstance(result, dict)
        assert "token" in result
        assert result["user"]["name"] == "Bruno"
        assert result["user"]["email"] == "bruno@exemplo.com"

        # Verifica token gerado
        payload = auth_util.verify_token(result["token"])
        assert payload is not None
        assert payload["userId"] == "123e4567-e89b-12d3-a456-426614174000"
        assert payload["name"] == "Bruno"
