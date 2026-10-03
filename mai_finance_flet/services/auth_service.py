"""
auth_service.py — Serviço de regras de negócio para autenticação de usuários.

Implementa o login de usuários na tabela `mai_finance_users`
utilizando o cliente Supabase e os algoritmos PBKDF2/JWT de db/auth.py.
"""
from __future__ import annotations

from typing import Any
import db.auth as auth_util
from db.supabase_client import get_client


def login_user(
    email: str,
    password: str,
    client: Any = None,
) -> tuple[bool, str | dict[str, Any]]:
    """
    Autentica um usuário existente com e-mail e senha.

    Retorna:
        (True, {"token": str, "user": {"id": str, "name": str, "email": str}}) em caso de sucesso.
        (False, "mensagem amigável de erro") em caso de falha.
    """
    if not email or not isinstance(email, str) or "@" not in email or "." not in email:
        return False, "Por favor, informe um e-mail válido."

    if not password or not isinstance(password, str) or len(password) < 8:
        return False, "A senha deve conter no mínimo 8 caracteres."

    clean_email = email.strip().lower()

    if client is None:
        client = get_client()

    try:
        response = (
            client.table("mai_finance_users")
            .select("id, name, email, password_hash")
            .eq("email", clean_email)
            .limit(1)
            .execute()
        )

        rows = response.data if hasattr(response, "data") else []
        if not rows:
            return False, "E-mail ou senha incorretos."

        user = rows[0]
        stored_hash = user.get("password_hash", "")

        if not auth_util.verify_password(password, stored_hash):
            return False, "E-mail ou senha incorretos."

        token = auth_util.create_token(
            user_id=str(user["id"]),
            name=user["name"],
            email=user["email"],
        )

        return True, {
            "token": token,
            "user": {
                "id": str(user["id"]),
                "name": user["name"],
                "email": user["email"],
            },
        }
    except Exception as exc:  # noqa: BLE001
        return False, f"Erro de comunicação com o servidor: {exc}"

