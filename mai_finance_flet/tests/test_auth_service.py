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
from services.auth_service import login_user, register_user


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

    def test_register_empty_name(self):
        ok, msg = register_user("", "user@example.com", "senha1234")
        assert not ok
        assert "nome de usuário" in msg

    def test_register_invalid_email(self):
        ok, msg = register_user("Bruno", "email_sem_arroba", "senha1234")
        assert not ok
        assert "e-mail válido" in msg

    def test_register_short_password(self):
        ok, msg = register_user("Bruno", "user@example.com", "curta")
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


class TestRegisterUser:
    """Testa o fluxo de cadastro com mock do Supabase (AC-004)."""

    def test_register_duplicate_email(self):
        """AC-004: e-mail existente retorna erro de duplicidade amigável."""
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        # Simula que já existe um usuário
        mock_query.execute.return_value = MagicMock(data=[{"id": "uuid-1"}])

        ok, msg = register_user("Bruno", "bruno@exemplo.com", "senha12345", client=mock_client)
        assert not ok
        assert msg == "Este e-mail já está cadastrado."

    def test_register_success(self):
        """AC-004: novos dados geram hash PBKDF2 e token de 24h."""
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.insert.return_value = mock_query

        # Primeira chamada (check): retorna []
        # Segunda chamada (insert): retorna [new_user]
        mock_query.execute.side_effect = [
            MagicMock(data=[]),  # check email
            MagicMock(data=[{
                "id": "new-uuid-999",
                "name": "Maria",
                "email": "maria@exemplo.com",
            }]),  # insert
        ]

        ok, result = register_user("Maria", "maria@exemplo.com", "senhaNovaSegura123", client=mock_client)
        assert ok
        assert isinstance(result, dict)
        assert "token" in result
        assert result["user"]["name"] == "Maria"

        # Verifica se o insert foi chamado com hash PBKDF2 (formato salt:hash)
        insert_calls = mock_query.insert.call_args_list
        assert len(insert_calls) == 1
        inserted_payload = insert_calls[0][0][0]
        assert inserted_payload["email"] == "maria@exemplo.com"
        assert ":" in inserted_payload["password_hash"]
        salt, h = inserted_payload["password_hash"].split(":")
        assert len(salt) == 32  # 16 bytes em hex
        assert len(h) == 128    # 64 bytes em hex (sha512)
