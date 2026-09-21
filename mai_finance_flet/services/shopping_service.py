"""
shopping_service.py — Lógica de negócio da Lista de Compras Inteligente.

Implementa:
- Gestão de itens agrupados por corredor
- Validações de entrada e catálogo de sugestões rápidas
- Métricas em tempo real do carrinho de compras
- Resiliência offline com cache local e fila de sincronização (AC-028)
"""
from __future__ import annotations

import logging
from typing import Any, Callable
from db.shopping import (
    list_shopping_items,
    create_shopping_item,
    update_shopping_item,
    delete_shopping_item,
    toggle_item_bought,
    clear_bought_items,
    save_shopping_history,
    list_frequent_items,
    record_frequent_item_usage,
)

logger = logging.getLogger(__name__)

CORRIDORS: list[str] = [
    "Hortifruti",
    "Carnes & Açougue",
    "Laticínios & Frios",
    "Mercearia & Padaria",
    "Bebidas",
    "Limpeza & Higiene",
    "Congelados",
    "Outros",
]

DEFAULT_UNITS: list[str] = ["un", "kg", "g", "cx", "pct", "l", "ml"]

DEFAULT_FREQUENT_ITEMS: list[dict[str, str]] = [
    {"name": "Leite", "unit": "cx", "corridor": "Laticínios & Frios"},
    {"name": "Café", "unit": "pct", "corridor": "Mercearia & Padaria"},
    {"name": "Arroz", "unit": "pct", "corridor": "Mercearia & Padaria"},
    {"name": "Feijão", "unit": "pct", "corridor": "Mercearia & Padaria"},
    {"name": "Açúcar", "unit": "pct", "corridor": "Mercearia & Padaria"},
    {"name": "Detergente", "unit": "un", "corridor": "Limpeza & Higiene"},
    {"name": "Banana", "unit": "kg", "corridor": "Hortifruti"},
    {"name": "Ovos", "unit": "cx", "corridor": "Laticínios & Frios"},
    {"name": "Pão", "unit": "un", "corridor": "Mercearia & Padaria"},
    {"name": "Sabão em Pó", "unit": "cx", "corridor": "Limpeza & Higiene"},
]

# Cache local em memória e fila de operações offline
_local_cache: list[dict[str, Any]] = []
_offline_mutation_queue: list[dict[str, Any]] = []


def get_corridors() -> list[str]:
    """Retorna lista de seções/corredores para categorização da compra."""
    return list(CORRIDORS)


def add_shopping_item(
    name: str,
    quantity: float = 1.0,
    unit: str = "un",
    corridor: str = "Outros",
    estimated_price: float = 0.0,
    market_name: str | None = None,
) -> dict[str, Any]:
    """Valida e cadastra um novo item na lista de compras."""
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValueError("O nome do item é obrigatório.")
    if quantity <= 0:
        quantity = 1.0

    valid_corridor = corridor.strip() if corridor and corridor.strip() in CORRIDORS else "Outros"
    valid_unit = unit.strip() if unit and unit.strip() in DEFAULT_UNITS else "un"

    payload = {
        "name": clean_name,
        "quantity": float(quantity),
        "unit": valid_unit,
        "corridor_category": valid_corridor,
        "is_bought": False,
        "estimated_price": float(estimated_price or 0.0),
        "actual_price": None,
        "market_name": market_name,
    }

    try:
        created = create_shopping_item(payload)
        if not created.get("id"):
            import uuid
            payload["id"] = str(uuid.uuid4())
            created = payload
        # Atualiza sugestões frequentes
        try:
            record_frequent_item_usage(clean_name, valid_unit, valid_corridor)
        except Exception as exc:
            logger.warning(f"Erro ao registrar item frequente: {exc}")
    except Exception as exc:
        logger.warning(f"Modo offline: gravando item localmente ({exc})")
        import uuid
        payload["id"] = str(uuid.uuid4())
        payload["_pending_sync"] = True
        _offline_mutation_queue.append({"action": "create", "data": payload})
        created = payload

    _update_cache_item(created)
    return created


def get_all_items() -> list[dict[str, Any]]:
    """Obtém todos os itens, sincronizando cache local com o Supabase."""
    global _local_cache
    try:
        items = list_shopping_items()
        _local_cache = items
        return items
    except Exception as exc:
        err_msg = str(exc)
        if "[WinError 10035]" not in err_msg and "WSAEWOULDBLOCK" not in err_msg:
            logger.warning(f"Falha ao conectar no Supabase, usando cache local: {exc}")
        else:
            logger.debug(f"I/O transitório do Windows, usando cache local: {exc}")
        return list(_local_cache)


def get_items_grouped_by_corridor(items: list[dict[str, Any]] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Agrupa a lista de itens por seção/corredor para navegação no mercado."""
    if items is None:
        items = get_all_items()

    grouped: dict[str, list[dict[str, Any]]] = {c: [] for c in CORRIDORS}
    for item in items:
        corridor = item.get("corridor_category", "Outros")
        if corridor not in grouped:
            grouped[corridor] = []
        grouped[corridor].append(item)

    # Retorna apenas corredores que possuem itens
    return {c: list_items for c, list_items in grouped.items() if list_items}


def calculate_cart_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula métricas agregadas da lista/carrinho de compras em tempo real."""
    total_count = len(items)
    bought_count = 0
    total_bought_amount = 0.0
    total_pending_amount = 0.0
    total_estimated_amount = 0.0

    for item in items:
        qty = float(item.get("quantity", 1.0) or 1.0)
        est_price = float(item.get("estimated_price", 0.0) or 0.0)
        act_price = float(item.get("actual_price", 0.0) or 0.0) if item.get("actual_price") is not None else None

        item_price = act_price if act_price is not None else est_price
        item_total = item_price * qty
        total_estimated_amount += (est_price * qty)

        if item.get("is_bought"):
            bought_count += 1
            total_bought_amount += item_total
        else:
            total_pending_amount += item_total

    pending_count = total_count - bought_count
    completion_pct = (bought_count / total_count * 100.0) if total_count > 0 else 0.0

    return {
        "total_count": total_count,
        "bought_count": bought_count,
        "pending_count": pending_count,
        "total_bought_amount": round(total_bought_amount, 2),
        "total_pending_amount": round(total_pending_amount, 2),
        "total_estimated_amount": round(total_estimated_amount, 2),
        "completion_pct": round(completion_pct, 1),
    }


def toggle_item_status(
    item_id: str,
    is_bought: bool,
    actual_price: float | None = None,
) -> dict[str, Any]:
    """
    Alterna o status 'OK' do item com suporte à resiliência offline (AC-028).
    Se a internet oscilar no mercado, persiste no cache local e enfileira para sincronizar.
    """
    global _local_cache
    updated_record: dict[str, Any] = {"id": item_id, "is_bought": is_bought}
    if actual_price is not None:
        updated_record["actual_price"] = actual_price

    # Atualiza cache local instantaneamente
    for idx, it in enumerate(_local_cache):
        if it.get("id") == item_id:
            _local_cache[idx]["is_bought"] = is_bought
            if actual_price is not None:
                _local_cache[idx]["actual_price"] = actual_price
            updated_record = dict(_local_cache[idx])
            break

    try:
        remote_res = toggle_item_bought(item_id, is_bought)
        if actual_price is not None:
            update_shopping_item(item_id, {"actual_price": actual_price})
        return remote_res or updated_record
    except Exception as exc:
        logger.warning(f"Rede instável: marcando item offline para sincronização posterior ({exc})")
        _offline_mutation_queue.append({
            "action": "toggle_bought",
            "item_id": item_id,
            "is_bought": is_bought,
            "actual_price": actual_price,
        })
        return updated_record


def sync_offline_queue() -> int:
    """Executa sincronização de mutações pendentes enfileiradas durante oscilações de sinal."""
    global _offline_mutation_queue
    if not _offline_mutation_queue:
        return 0

    synced = 0
    remaining_queue: list[dict[str, Any]] = []

    for mut in _offline_mutation_queue:
        try:
            if mut["action"] == "toggle_bought":
                toggle_item_bought(mut["item_id"], mut["is_bought"])
                if mut.get("actual_price") is not None:
                    update_shopping_item(mut["item_id"], {"actual_price": mut["actual_price"]})
                synced += 1
            elif mut["action"] == "create":
                item_data = mut["data"]
                item_data.pop("_pending_sync", None)
                create_shopping_item(item_data)
                synced += 1
        except Exception as exc:
            logger.error(f"Falha ao sincronizar mutação pendente: {exc}")
            remaining_queue.append(mut)

    _offline_mutation_queue = remaining_queue
    return synced


def get_pending_offline_count() -> int:
    """Retorna quantidade de ações aguardando sincronização com o banco."""
    return len(_offline_mutation_queue)


def get_quick_suggestions() -> list[dict[str, str]]:
    """Retorna lista combinada de itens frequentes gravados no banco e padrões do sistema (AC-022)."""
    suggestions: list[dict[str, str]] = []
    seen_names: set[str] = set()

    try:
        db_frequents = list_frequent_items()
        for it in db_frequents:
            name = it.get("name", "").strip()
            if name and name.lower() not in seen_names:
                seen_names.add(name.lower())
                suggestions.append({
                    "name": name,
                    "unit": it.get("default_unit", "un"),
                    "corridor": it.get("corridor_category", "Outros"),
                })
    except Exception as exc:
        logger.warning(f"Erro ao listar itens frequentes do banco: {exc}")

    # Completa com itens frequentes padrão para garantir variedade de atalhos rápidos
    for def_it in DEFAULT_FREQUENT_ITEMS:
        name = def_it.get("name", "").strip()
        if name.lower() not in seen_names:
            seen_names.add(name.lower())
            suggestions.append(def_it)

    return suggestions


def _update_cache_item(item: dict[str, Any]) -> None:
    """Atualiza ou insere item no cache local."""
    global _local_cache
    for idx, it in enumerate(_local_cache):
        if it.get("id") == item.get("id"):
            _local_cache[idx] = item
            return
    _local_cache.append(item)
