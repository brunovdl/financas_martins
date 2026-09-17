"""
auth.py — Autenticação do MAI Finance Flet.

Implementa exatamente o mesmo algoritmo do Next.js original (lib/auth.ts):
- Hashing: PBKDF2-HMAC-SHA512, 1000 iterações, salt de 16 bytes aleatórios.
  O salt é convertido para hex e usado COMO STRING na função de derivação
  (igual ao Node.js: `crypto.pbkdf2Sync(password, saltHexString, 1000, 64, 'sha512')`).
- Formato armazenado: "<salt_hex>:<hash_hex>" (campo password_hash do banco).
- JWT: HMAC-SHA256 manual (igual ao Next.js) — não usa PyJWT para manter
  compatibilidade de tokens entre as versões (mobile app / web app).
  Campos: userId, name, email, iat, exp (24h).

ATENÇÃO: o algoritmo DEVE ser idêntico ao original — os usuários existentes
no banco têm hashes nesse formato. Qualquer divergência quebra o login.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

# ---------------------------------------------------------------------------
# Hashing de senha — PBKDF2-HMAC-SHA512
# ---------------------------------------------------------------------------

_ITERATIONS = 1000
_HASH_NAME = "sha512"
_KEY_LENGTH = 64  # bytes de saída (igual ao Node.js: length=64)
_SALT_BYTES = 16


def hash_password(plain: str) -> str:
    """
    Gera um hash PBKDF2 de uma nova senha.
    Retorna no formato '<salt_hex>:<hash_hex>'.

    PARIDADE com Node.js:
      const salt = crypto.randomBytes(16).toString('hex')  → salt é STRING hex (32 chars)
      crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512') → salt é encodado como UTF-8
    """
    salt_bytes = os.urandom(_SALT_BYTES)
    salt_hex = salt_bytes.hex()  # ex.: 'a3f2...'
    # O Node.js passa a STRING hex como salt (não os bytes raw)
    dk = hashlib.pbkdf2_hmac(_HASH_NAME, plain.encode("utf-8"), salt_hex.encode("utf-8"), _ITERATIONS, dklen=_KEY_LENGTH)
    return f"{salt_hex}:{dk.hex()}"


def verify_password(plain: str, stored_hash: str) -> bool:
    """
    Verifica se `plain` corresponde ao `stored_hash` no formato '<salt_hex>:<hash_hex>'.
    Compatível com todos os hashes já armazenados no banco (gerados pelo Next.js).
    Retorna True se correto, False caso contrário.
    """
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)
        expected = bytes.fromhex(hash_hex)
        # Usa a STRING hex do salt (igual ao Node.js)
        dk = hashlib.pbkdf2_hmac(_HASH_NAME, plain.encode("utf-8"), salt_hex.encode("utf-8"), _ITERATIONS, dklen=_KEY_LENGTH)
        # Comparação em tempo constante
        return hmac.compare_digest(dk, expected)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT — HMAC-SHA256 manual (compatível com o JWT caseiro do Next.js)
# ---------------------------------------------------------------------------


def _b64url_encode(data: bytes | str) -> str:
    """Codifica em base64url sem padding."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Decodifica base64url com padding restaurado."""
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def create_token(user_id: str, name: str, email: str) -> str:
    """
    Cria um JWT HS256 com expiração de 24h.
    Campos: userId, name, email, iat, exp — idênticos ao payload do Next.js.
    Implementação HMAC manual compatível com lib/auth.ts createToken().
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "userId": user_id,
        "name": name,
        "email": email,
        "iat": now,
        "exp": now + config.SESSION_DURATION_SECONDS,
    }
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        config.JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_token(token: str) -> dict | None:
    """
    Verifica e decodifica um JWT.
    Retorna o payload se válido e não expirado, None caso contrário.
    Implementação compatível com lib/auth.ts verifyToken().
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, signature = parts
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected_sig = hmac.new(
            config.JWT_SECRET.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        # Comparação em tempo constante
        if not hmac.compare_digest(
            _b64url_decode(signature),
            expected_sig,
        ):
            return None
        payload = json.loads(_b64url_decode(encoded_payload))
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None  # Sessão expirada
        return payload
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Validação de senha mínima
# ---------------------------------------------------------------------------

MIN_PASSWORD_LENGTH = 8


def validate_password_strength(plain: str) -> str | None:
    """
    Valida força mínima da senha.
    Retorna None se válida, ou uma mensagem de erro se inválida.
    """
    if len(plain) < MIN_PASSWORD_LENGTH:
        return f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres."
    return None
