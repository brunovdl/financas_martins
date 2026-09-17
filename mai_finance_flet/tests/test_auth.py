"""
test_auth.py — Testes do módulo de autenticação (T-002).

Cobre os critérios de aceite:
- AC-001: Login com credenciais existentes retorna sessão válida
- AC-002: verify_password compatível com hashes legados (gerados pelo Node.js)
- AC-003: Sessão expira após 24h
- AC-004: Senha mínima de 8 caracteres no cadastro
"""
import os
import time

import pytest

# Configura variáveis de ambiente mínimas para o config.py não falhar no import
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from db.auth import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    validate_password_strength,
    MIN_PASSWORD_LENGTH,
)


# ---------------------------------------------------------------------------
# AC-002 — Função verify_password compatível com hashes legados
# @spec:AC-002
# ---------------------------------------------------------------------------

class TestVerifyPassword:
    """@spec:AC-002 — Compatibilidade com hashes PBKDF2-HMAC-SHA512 do Next.js."""

    def test_hash_and_verify_roundtrip(self):
        """Hash gerado por hash_password deve ser verificado corretamente."""
        plain = "minhasenha123"
        stored = hash_password(plain)
        assert verify_password(plain, stored), "verify_password deve retornar True para a senha correta"

    def test_wrong_password_returns_false(self):
        """Senha errada deve retornar False."""
        stored = hash_password("senhaCorreta")
        assert not verify_password("senhaErrada", stored), "Senha errada deve retornar False"

    def test_empty_password_returns_false(self):
        """Senha vazia deve retornar False."""
        stored = hash_password("senhaCorreta")
        assert not verify_password("", stored)

    def test_malformed_hash_returns_false(self):
        """Hash malformado deve retornar False sem exceção."""
        assert not verify_password("qualquercoisa", "hash_sem_dois_pontos")
        assert not verify_password("qualquercoisa", "")
        assert not verify_password("qualquercoisa", ":semhash")

    def test_hash_format_is_salt_colon_hash(self):
        """Hash gerado deve estar no formato '<hex>:<hex>'."""
        stored = hash_password("teste")
        parts = stored.split(":")
        assert len(parts) == 2, "Formato deve ser 'salt_hex:hash_hex'"
        salt_hex, hash_hex = parts
        assert len(salt_hex) == 32, "Salt hex deve ter 32 chars (16 bytes)"
        assert len(hash_hex) == 128, "Hash hex deve ter 128 chars (64 bytes = SHA-512)"

    def test_node_js_compatible_hash(self):
        """
        Testa paridade com o algoritmo do Node.js.
        
        Hash gerado em Node.js com:
          const salt = crypto.randomBytes(16).toString('hex')
          → salt = 'a1b2c3d4e5f60708090a0b0c0d0e0f10' (exemplo fixo)
          const hash = crypto.pbkdf2Sync('senha123', salt, 1000, 64, 'sha512').toString('hex')
        
        Para validar: executar o snippet Node.js e colar o hash resultante aqui.
        Este teste usa um hash gerado pela nossa implementação Python e verifica
        a consistência interna (o hash cross-language requer um hash real do banco).
        """
        import hashlib
        # Replica o que o Node.js faz: salt é a STRING hex, não os bytes
        salt_hex = "a1b2c3d4e5f60708090a0b0c0d0e0f10"
        password = "senha123"
        dk = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt_hex.encode("utf-8"), 1000, dklen=64)
        stored = f"{salt_hex}:{dk.hex()}"
        assert verify_password(password, stored), "Deve verificar hash gerado com salt como string hex"
        assert not verify_password("senhaErrada", stored)


# ---------------------------------------------------------------------------
# AC-001 / AC-003 — Token JWT: criação, verificação, expiração
# @spec:AC-001
# @spec:AC-003
# ---------------------------------------------------------------------------

class TestJWT:
    """@spec:AC-001 @spec:AC-003 — JWT HS256 com campos corretos e expiração."""

    def test_create_token_returns_string(self):
        """create_token deve retornar uma string JWT."""
        token = create_token("uuid-123", "Bruno", "bruno@example.com")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3, "JWT deve ter 3 partes separadas por ponto"

    def test_token_payload_fields(self):
        """@spec:AC-001 — Token deve conter campos userId, name, email, iat, exp."""
        token = create_token("uuid-abc", "Bruno", "bruno@example.com")
        payload = verify_token(token)
        assert payload is not None, "Token válido deve ser decodificado"
        assert payload["userId"] == "uuid-abc"
        assert payload["name"] == "Bruno"
        assert payload["email"] == "bruno@example.com"
        assert "iat" in payload
        assert "exp" in payload

    def test_token_expires_after_24h(self):
        """@spec:AC-003 — Token expirado deve retornar None."""
        import json, base64, hmac, hashlib

        # Cria token com exp no passado
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload_data = {
            "userId": "uuid-exp",
            "name": "Expired",
            "email": "exp@test.com",
            "iat": now - 90000,
            "exp": now - 3600,  # expirado há 1h
        }
        secret = os.environ["JWT_SECRET"]

        def b64url(data):
            if isinstance(data, str):
                data = data.encode()
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        enc_h = b64url(json.dumps(header, separators=(",", ":")))
        enc_p = b64url(json.dumps(payload_data, separators=(",", ":")))
        signing = f"{enc_h}.{enc_p}"
        sig = hmac.new(secret.encode(), signing.encode(), hashlib.sha256).digest()
        expired_token = f"{signing}.{b64url(sig)}"

        result = verify_token(expired_token)
        assert result is None, "Token expirado deve retornar None"

    def test_invalid_token_returns_none(self):
        """Token inválido/corrompido deve retornar None."""
        assert verify_token("nao.e.um.jwt.valido") is None
        assert verify_token("") is None
        assert verify_token("abc.def.ghi") is None  # assinatura inválida


# ---------------------------------------------------------------------------
# AC-004 — Validação de senha mínima
# @spec:AC-004
# ---------------------------------------------------------------------------

class TestPasswordValidation:
    """@spec:AC-004 — Senha mínima de 8 caracteres no cadastro."""

    def test_short_password_returns_error(self):
        """Senha com menos de 8 chars deve retornar mensagem de erro."""
        result = validate_password_strength("1234567")
        assert result is not None, "Deve retornar erro para senha curta"
        assert "8" in result or "caracteres" in result.lower()

    def test_exact_minimum_length_is_valid(self):
        """Senha com exatamente 8 chars deve ser válida."""
        result = validate_password_strength("12345678")
        assert result is None, "8 caracteres deve ser aceito"

    def test_long_password_is_valid(self):
        """Senha longa deve ser válida."""
        result = validate_password_strength("senhaForteESegura2026!")
        assert result is None

    def test_empty_password_is_invalid(self):
        """Senha vazia deve retornar erro."""
        result = validate_password_strength("")
        assert result is not None

    def test_min_password_length_constant(self):
        """Constante MIN_PASSWORD_LENGTH deve ser 8."""
        assert MIN_PASSWORD_LENGTH == 8
