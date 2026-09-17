"""
categories.py — Serviço de regras de negócio e persistência de categorias.

Implementa:
- Listagem, criação, atualização e exclusão de categorias (AC-010, AC-011)
- Validação de unicidade de nome de categoria (AC-010)
- Desvinculação de despesas (SET category_id = NULL) antes da exclusão (AC-011)
- Coluna de cor 'color' conforme schema.sql
"""
from __future__ import annotations

from typing import Any
from db.supabase_client import get_client


def _normalize_cat(cat: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cat, dict):
        return cat
    c = dict(cat)
    col = c.get("color") or c.get("color_hex") or "#94A3B8"
    c["color"] = col
    c["color_hex"] = col
    return c


def list_categories(client: Any = None) -> list[dict[str, Any]]:
    """
    Lista todas as categorias cadastradas, ordenadas por nome.
    """
    if client is None:
        client = get_client()

    response = client.table("categories").select("*").order("name").execute()
    rows = response.data if hasattr(response, "data") and response.data else []
    return [_normalize_cat(r) for r in rows]


def get_category_by_name(name: str, client: Any = None) -> dict[str, Any] | None:
    """Busca uma categoria pelo nome (case-insensitive)."""
    if client is None:
        client = get_client()

    clean_name = name.strip()
    if not clean_name:
        return None

    response = client.table("categories").select("*").ilike("name", clean_name).limit(1).execute()
    rows = response.data if hasattr(response, "data") and response.data else []
    return _normalize_cat(rows[0]) if rows else None


def create_category(name: str, color: str = "#94A3B8", client: Any = None) -> dict[str, Any]:
    """
    Cria uma nova categoria com nome único e cor hex (AC-010).
    Lança ValueError se o nome já estiver em uso.
    """
    if client is None:
        client = get_client()

    clean_name = name.strip()
    if not clean_name:
        raise ValueError("O nome da categoria é obrigatório.")

    clean_color = color.strip() or "#94A3B8"

    # Validação de unicidade prévia
    existing = get_category_by_name(clean_name, client=client)
    if existing:
        raise ValueError("Já existe uma categoria com este nome.")

    payload = {
        "name": clean_name,
        "color": clean_color,
    }

    try:
        response = client.table("categories").insert(payload).select("*").execute()
        rows = response.data if hasattr(response, "data") and response.data else []
        if not rows:
            raise RuntimeError("Falha ao criar categoria no banco de dados.")
        return rows[0]
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Já existe uma categoria com este nome.") from exc
        raise


def update_category(category_id: str, name: str, color: str, client: Any = None) -> dict[str, Any]:
    """
    Atualiza o nome e a cor de uma categoria existente.
    Valida duplicidade de nome em relação a outras categorias.
    """
    if client is None:
        client = get_client()

    clean_name = name.strip()
    if not clean_name:
        raise ValueError("O nome da categoria é obrigatório.")

    clean_color = color.strip() or "#94A3B8"

    # Verifica se outra categoria já usa esse nome
    existing = get_category_by_name(clean_name, client=client)
    if existing and str(existing.get("id")) != str(category_id):
        raise ValueError("Já existe uma categoria com este nome.")

    payload = {
        "name": clean_name,
        "color": clean_color,
    }

    try:
        response = (
            client.table("categories")
            .update(payload)
            .eq("id", category_id)
            .select("*")
            .execute()
        )
        rows = response.data if hasattr(response, "data") and response.data else []
        if not rows:
            raise RuntimeError(f"Categoria {category_id} não encontrada para atualização.")
        return rows[0]
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise ValueError("Já existe uma categoria com este nome.") from exc
        raise


def delete_category(category_id: str, client: Any = None) -> bool:
    """
    Exclui uma categoria desvinculando previamente as despesas associadas (AC-011).
    Garante que despesas vinculadas fiquem com category_id = NULL e não sejam apagadas.
    """
    if client is None:
        client = get_client()

    # 1. Desvincula despesas da categoria (AC-011)
    client.table("expenses").update({"category_id": None}).eq("category_id", category_id).execute()

    # 2. Exclui a categoria
    response = client.table("categories").delete().eq("id", category_id).execute()
    return bool(hasattr(response, "data"))
