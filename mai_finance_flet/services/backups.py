"""
backups.py — Serviço de criação, listagem e restauração de snapshots de backup.

Implementa:
- Listagem dos snapshots existentes ordenados por data decrescente (AC-014)
- Criação de backup manual via RPC do Supabase 'create_backup' (AC-014)
- Restauração de snapshot JSONB repovoando categories e expenses (AC-015)
"""
from __future__ import annotations

from typing import Any
from db.supabase_client import get_client


def list_backups(client: Any = None) -> list[dict[str, Any]]:
    """
    Lista todos os backups registrados, ordenados do mais recente para o mais antigo.
    """
    if client is None:
        client = get_client()

    response = client.table("backups").select("*").order("created_at", desc=True).execute()
    return response.data if hasattr(response, "data") and response.data else []


def create_manual_backup(client: Any = None) -> str:
    """
    Dispara a função armazenada create_backup('manual') via RPC do Supabase (AC-014).
    Retorna o UUID do backup gerado.
    """
    if client is None:
        client = get_client()

    response = client.rpc("create_backup", {"backup_type": "manual"}).execute()
    backup_id = response.data if hasattr(response, "data") else None
    return str(backup_id) if backup_id else ""


_DELETE_CHUNK = 100


def _fetch_ids(client: Any, table: str) -> set[str]:
    response = client.table(table).select("id").execute()
    rows = response.data if hasattr(response, "data") and isinstance(response.data, list) else []
    return {str(r.get("id")) for r in rows if isinstance(r, dict) and r.get("id")}


def _delete_ids(client: Any, table: str, ids: set[str]) -> None:
    pending = sorted(ids)
    for i in range(0, len(pending), _DELETE_CHUNK):
        client.table(table).delete().in_("id", pending[i:i + _DELETE_CHUNK]).execute()


def restore_backup(backup_id: str, client: Any = None) -> dict[str, int]:
    """
    Restaura o banco de dados a partir do snapshot JSONB do backup selecionado (AC-015).

    Ordem pensada para nunca deixar as tabelas vazias se algo falhar no meio:
    1. Remove somente os registros que NÃO existem no snapshot (despesas, depois categorias,
       liberando nomes únicos de categoria que o snapshot vai reutilizar);
    2. Faz upsert (por id) das categorias e despesas do snapshot.
    Registros em comum nunca são apagados — no pior caso a restauração fica parcial,
    e repeti-la conclui o processo.
    """
    if client is None:
        client = get_client()

    # 1. Busca o snapshot
    response = client.table("backups").select("*").eq("id", backup_id).limit(1).execute()
    rows = response.data if hasattr(response, "data") and response.data else []
    if not rows:
        raise ValueError(f"Backup com ID {backup_id} não encontrado.")

    snapshot = rows[0]
    data = snapshot.get("data") or {}
    categories_snapshot = data.get("categories") or []
    expenses_snapshot = data.get("expenses") or []

    cats_payload = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "color": c.get("color") or c.get("color_hex") or "#94A3B8",
        }
        for c in categories_snapshot
    ]
    exps_payload = [
        {
            "id": e.get("id"),
            "due_date": str(e.get("due_date")),
            "category_id": e.get("category_id") or None,
            "description": e.get("description") or "",
            "amount": float(e.get("amount") or 0.0),
            "payment_date": str(e.get("payment_date")) if e.get("payment_date") else None,
            "status": e.get("status") or "pendente",
            "observation": e.get("observation") or None,
            "month_ref": str(e.get("month_ref")),
        }
        for e in expenses_snapshot
    ]

    # 2. Remove apenas o que não faz parte do snapshot (despesas primeiro por FK)
    snapshot_exp_ids = {str(e["id"]) for e in exps_payload if e.get("id")}
    snapshot_cat_ids = {str(c["id"]) for c in cats_payload if c.get("id")}
    _delete_ids(client, "expenses", _fetch_ids(client, "expenses") - snapshot_exp_ids)
    _delete_ids(client, "categories", _fetch_ids(client, "categories") - snapshot_cat_ids)

    # 3. Upsert das categorias
    cats_restored = 0
    if cats_payload:
        cat_res = client.table("categories").upsert(cats_payload, on_conflict="id").execute()
        if hasattr(cat_res, "data") and isinstance(cat_res.data, list) and cat_res.data:
            cats_restored = len(cat_res.data)
        else:
            cats_restored = len(cats_payload)

    # 4. Upsert das despesas
    exps_restored = 0
    if exps_payload:
        exp_res = client.table("expenses").upsert(exps_payload, on_conflict="id").execute()
        if hasattr(exp_res, "data") and isinstance(exp_res.data, list) and exp_res.data:
            exps_restored = len(exp_res.data)
        else:
            exps_restored = len(exps_payload)

    return {
        "categories_restored": cats_restored,
        "expenses_restored": exps_restored,
    }
