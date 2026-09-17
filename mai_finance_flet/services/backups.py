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


def restore_backup(backup_id: str, client: Any = None) -> dict[str, int]:
    """
    Restaura o banco de dados a partir do snapshot JSONB do backup selecionado (AC-015).
    Limpa as tabelas 'expenses' e 'categories' e repopula os registros preservando IDs.
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

    # 2. Limpa registros existentes (despesas primeiro por dependência de FK)
    client.table("expenses").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    client.table("categories").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    # 3. Restaura categorias
    cats_restored = 0
    if categories_snapshot:
        cats_payload = []
        for c in categories_snapshot:
            cats_payload.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "color": c.get("color") or c.get("color_hex") or "#94A3B8",
            })
        cat_res = client.table("categories").insert(cats_payload).execute()
        if hasattr(cat_res, "data") and cat_res.data:
            cats_restored = len(cat_res.data)
        else:
            cats_restored = len(cats_payload)

    # 4. Restaura despesas
    exps_restored = 0
    if expenses_snapshot:
        exps_payload = []
        for e in expenses_snapshot:
            exps_payload.append({
                "id": e.get("id"),
                "due_date": str(e.get("due_date")),
                "category_id": e.get("category_id") or None,
                "description": e.get("description") or "",
                "amount": float(e.get("amount") or 0.0),
                "payment_date": str(e.get("payment_date")) if e.get("payment_date") else None,
                "status": e.get("status") or "pendente",
                "observation": e.get("observation") or None,
                "month_ref": str(e.get("month_ref")),
            })
        exp_res = client.table("expenses").insert(exps_payload).execute()
        if hasattr(exp_res, "data") and exp_res.data:
            exps_restored = len(exp_res.data)
        else:
            exps_restored = len(exps_payload)

    return {
        "categories_restored": cats_restored,
        "expenses_restored": exps_restored,
    }
