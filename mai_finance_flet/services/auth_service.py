"""
auth_service.py — Serviço de regras de negócio para autenticação de usuários.

Implementa login e cadastro de usuários na tabela `mai_finance_users`
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


def register_user(
    name: str,
    email: str,
    password: str,
    client: Any = None,
) -> tuple[bool, str | dict[str, Any]]:
    """
    Cadastra um novo usuário no sistema.

    Retorna:
        (True, {"token": str, "user": {"id": str, "name": str, "email": str}}) em caso de sucesso.
        (False, "mensagem amigável de erro") em caso de falha ou duplicidade.
    """
    clean_name = name.strip() if isinstance(name, str) else ""
    if not clean_name:
        return False, "Por favor, insira o seu nome de usuário."

    if not email or not isinstance(email, str) or "@" not in email or "." not in email:
        return False, "Por favor, informe um e-mail válido."

    if not password or not isinstance(password, str) or len(password) < 8:
        return False, "A senha deve conter no mínimo 8 caracteres."

    clean_email = email.strip().lower()

    if client is None:
        client = get_client()

    try:
        # 1. Verifica se o e-mail já existe
        check_response = (
            client.table("mai_finance_users")
            .select("id")
            .eq("email", clean_email)
            .limit(1)
            .execute()
        )
        existing = check_response.data if hasattr(check_response, "data") else []
        if existing:
            return False, "Este e-mail já está cadastrado."

        # 2. Gera hash PBKDF2 e insere novo usuário
        password_hash = auth_util.hash_password(password)
        insert_response = (
            client.table("mai_finance_users")
            .insert({
                "name": clean_name,
                "email": clean_email,
                "password_hash": password_hash,
            })
            .execute()
        )

        inserted_rows = insert_response.data if hasattr(insert_response, "data") else []
        if not inserted_rows:
            # Fallback para buscar o recém inserido
            fetch_response = (
                client.table("mai_finance_users")
                .select("id, name, email")
                .eq("email", clean_email)
                .limit(1)
                .execute()
            )
            inserted_rows = fetch_response.data if hasattr(fetch_response, "data") else []

        if not inserted_rows:
            return False, "Erro ao criar conta no banco de dados."

        new_user = inserted_rows[0]
        token = auth_util.create_token(
            user_id=str(new_user["id"]),
            name=new_user.get("name", clean_name),
            email=new_user.get("email", clean_email),
        )

        return True, {
            "token": token,
            "user": {
                "id": str(new_user["id"]),
                "name": new_user.get("name", clean_name),
                "email": new_user.get("email", clean_email),
            },
        }
    except Exception as exc:  # noqa: BLE001
        return False, f"Erro ao criar conta: {exc}"
