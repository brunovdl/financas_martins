"""
shopping.py — Acesso ao banco de dados Supabase para a Lista de Compras.

Tabelas gerenciadas:
- shopping_items: itens ativos na lista semanal
- shopping_history: histórico de compras finalizadas
- shopping_frequent_items: catálogo de sugestões e itens frequentes
"""
from __future__ import annotations

from typing import Any
from db.supabase_client import get_client


def _safe_execute(query_builder: Any, max_retries: int = 3) -> Any:
    """Executa a query com tolerância e retry automático a erros transitórios de socket no Windows (WinError 10035)."""
    import time
    for attempt in range(max_retries):
        try:
            return query_builder.execute()
        except (BlockingIOError, OSError, Exception) as exc:
            err_str = str(exc)
            is_transient = (
                isinstance(exc, BlockingIOError)
                or (hasattr(exc, "winerror") and exc.winerror == 10035)
                or "[WinError 10035]" in err_str
                or "WSAEWOULDBLOCK" in err_str
            )
            if is_transient and attempt < max_retries - 1:
                time.sleep(0.15 * (attempt + 1))
                continue
            raise exc


def list_shopping_items() -> list[dict[str, Any]]:
    """Retorna todos os itens da lista de compras ativa ordenados por corredor e data."""
    client = get_client()
    query = (
        client.table("shopping_items")
        .select("*")
        .order("corridor_category")
        .order("created_at")
    )
    res = _safe_execute(query)
    return res.data or []


def create_shopping_item(item_data: dict[str, Any]) -> dict[str, Any]:
    """Cria um novo item na lista de compras ativa."""
    client = get_client()
    payload = {
        "name": item_data.get("name", "").strip(),
        "quantity": float(item_data.get("quantity", 1.0)),
        "unit": item_data.get("unit", "un").strip(),
        "corridor_category": item_data.get("corridor_category", "Geral").strip(),
        "is_bought": bool(item_data.get("is_bought", False)),
        "estimated_price": float(item_data.get("estimated_price", 0.0) or 0.0),
        "actual_price": float(item_data["actual_price"]) if item_data.get("actual_price") is not None else None,
        "market_name": item_data.get("market_name"),
    }
    res = _safe_execute(client.table("shopping_items").insert(payload))
    if res.data and len(res.data) > 0:
        return res.data[0]
    return {}


def update_shopping_item(item_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Atualiza dados de um item existente na lista."""
    client = get_client()
    clean_updates: dict[str, Any] = {}
    if "name" in updates:
        clean_updates["name"] = updates["name"].strip()
    if "quantity" in updates:
        clean_updates["quantity"] = float(updates["quantity"])
    if "unit" in updates:
        clean_updates["unit"] = updates["unit"].strip()
    if "corridor_category" in updates:
        clean_updates["corridor_category"] = updates["corridor_category"].strip()
    if "is_bought" in updates:
        clean_updates["is_bought"] = bool(updates["is_bought"])
    if "estimated_price" in updates:
        clean_updates["estimated_price"] = float(updates["estimated_price"] or 0.0)
    if "actual_price" in updates:
        clean_updates["actual_price"] = (
            float(updates["actual_price"]) if updates["actual_price"] is not None else None
        )
    if "market_name" in updates:
        clean_updates["market_name"] = updates["market_name"]

    res = _safe_execute(client.table("shopping_items").update(clean_updates).eq("id", item_id))
    if res.data and len(res.data) > 0:
        return res.data[0]
    return {}


def delete_shopping_item(item_id: str) -> bool:
    """Remove um item da lista ativa."""
    client = get_client()
    res = _safe_execute(client.table("shopping_items").delete().eq("id", item_id))
    return bool(res.data)


def toggle_item_bought(item_id: str, is_bought: bool) -> dict[str, Any]:
    """Alterna o status de 'OK' (comprado) de um item."""
    return update_shopping_item(item_id, {"is_bought": is_bought})


def clear_bought_items() -> int:
    """Remove todos os itens marcados como comprados da lista ativa."""
    client = get_client()
    res = _safe_execute(client.table("shopping_items").delete().eq("is_bought", True))
    return len(res.data or [])


def clear_all_items() -> int:
    """Limpa todos os itens da lista ativa."""
    client = get_client()
    res = _safe_execute(client.table("shopping_items").delete().neq("id", "00000000-0000-0000-0000-000000000000"))
    return len(res.data or [])


def save_shopping_history(
    total_amount: float,
    market_name: str | None,
    items_count: int,
    items_snapshot: list[dict[str, Any]],
    expense_id: str | None = None,
) -> dict[str, Any]:
    """Arquiva uma compra finalizada no histórico."""
    client = get_client()
    payload = {
        "total_amount": float(total_amount),
        "market_name": market_name,
        "items_count": int(items_count),
        "items_snapshot": items_snapshot,
        "expense_id": expense_id,
    }
    res = _safe_execute(client.table("shopping_history").insert(payload))
    if res.data and len(res.data) > 0:
        return res.data[0]
    return {}


def list_shopping_history(limit: int = 20) -> list[dict[str, Any]]:
    """Recupera o histórico de compras anteriores."""
    client = get_client()
    query = (
        client.table("shopping_history")
        .select("*")
        .order("closed_at", desc=True)
        .limit(limit)
    )
    res = _safe_execute(query)
    return res.data or []


def list_frequent_items() -> list[dict[str, Any]]:
    """Lista sugestões de itens frequentes ordenadas pela frequência de uso."""
    client = get_client()
    query = (
        client.table("shopping_frequent_items")
        .select("*")
        .order("usage_count", desc=True)
        .limit(30)
    )
    res = _safe_execute(query)
    return res.data or []


def record_frequent_item_usage(
    name: str,
    default_unit: str = "un",
    corridor_category: str = "Geral",
) -> None:
    """Registra ou incrementa o uso de um item frequente."""
    client = get_client()
    clean_name = name.strip()
    if not clean_name:
        return
    existing = _safe_execute(
        client.table("shopping_frequent_items")
        .select("id, usage_count")
        .ilike("name", clean_name)
    )
    if existing.data and len(existing.data) > 0:
        item = existing.data[0]
        _safe_execute(
            client.table("shopping_frequent_items").update({
                "usage_count": item["usage_count"] + 1,
                "default_unit": default_unit,
                "corridor_category": corridor_category,
            }).eq("id", item["id"])
        )
    else:
        _safe_execute(
            client.table("shopping_frequent_items").insert({
                "name": clean_name,
                "default_unit": default_unit,
                "corridor_category": corridor_category,
                "usage_count": 1,
            })
        )
