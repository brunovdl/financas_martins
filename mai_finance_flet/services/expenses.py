"""
expenses.py — Serviço de regras de negócio e persistência de despesas.

Implementa listagem, CRUD, cálculo de resumo mensal e alternância de status
em paridade exata com a especificação e com o backend Supabase.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from db.supabase_client import get_client


def month_ref_to_date(month_ref: str) -> str:
    """Converte 'AAAA-MM' para 'AAAA-MM-01'."""
    if len(month_ref) == 7:
        return f"{month_ref}-01"
    return month_ref


def date_to_month_ref(iso_date: str) -> str:
    """Converte 'AAAA-MM-01' para 'AAAA-MM'."""
    return iso_date[:7]


def list_expenses(month_ref: str, client: Any = None) -> list[dict[str, Any]]:
    """
    Lista as despesas de um determinado mês de referência (AC-005).
    Ordenadas por data de vencimento (due_date) crescente.
    """
    if client is None:
        client = get_client()

    month_date = month_ref_to_date(month_ref)
    response = (
        client.table("expenses")
        .select("*, category:categories(*)")
        .eq("month_ref", month_date)
        .order("due_date", desc=False)
        .order("created_at", desc=False)
        .order("id", desc=False)
        .execute()
    )
    return response.data if hasattr(response, "data") and response.data else []


def get_monthly_summary(month_ref: str, client: Any = None) -> dict[str, Any]:
    """
    Obtém o resumo mensal a partir da view `monthly_summary` (AC-006, AC-007).
    Calcula total_pago e porcentagem paga para alimentação do dashboard.
    """
    if client is None:
        client = get_client()

    month_date = month_ref_to_date(month_ref)

    try:
        response = (
            client.table("monthly_summary")
            .select("*")
            .eq("month_ref", month_date)
            .limit(1)
            .execute()
        )
        rows = response.data if hasattr(response, "data") and response.data else []
        if rows:
            row = rows[0]
            total_despesas = float(row.get("total_despesas") or 0.0)
            total_pendente = float(row.get("total_pendente") or 0.0)
            qtd_pendente = int(row.get("qtd_pendente") or 0)
        else:
            total_despesas = 0.0
            total_pendente = 0.0
            qtd_pendente = 0
    except Exception:
        # Fallback se a view não estiver acessível ou sem dados
        total_despesas = 0.0
        total_pendente = 0.0
        qtd_pendente = 0

    total_pago = max(0.0, total_despesas - total_pendente)
    percent_pago = (total_pago / total_despesas * 100.0) if total_despesas > 0 else 100.0

    return {
        "month_ref": month_date,
        "total_despesas": total_despesas,
        "total_pago": total_pago,
        "total_pendente": total_pendente,
        "qtd_pendente": qtd_pendente,
        "percent_pago": percent_pago,
    }


def create_expense(expense_data: dict[str, Any], client: Any = None) -> dict[str, Any]:
    """
    Cria uma nova despesa no banco de dados (AC-008).
    Valida campos obrigatórios: description, due_date, amount, month_ref.
    """
    if client is None:
        client = get_client()

    description = (expense_data.get("description") or "").strip()
    if not description:
        raise ValueError("A descrição da despesa é obrigatória.")

    due_date = expense_data.get("due_date")
    if not due_date:
        raise ValueError("A data de vencimento é obrigatória.")

    amount = float(expense_data.get("amount") or 0.0)
    if amount < 0:
        raise ValueError("O valor da despesa não pode ser negativo.")

    raw_month = expense_data.get("month_ref") or date_to_month_ref(str(due_date))
    month_date = month_ref_to_date(raw_month)

    payload = {
        "description": description,
        "due_date": str(due_date),
        "amount": amount,
        "category_id": expense_data.get("category_id") or None,
        "status": expense_data.get("status", "pendente"),
        "payment_date": expense_data.get("payment_date") or None,
        "observation": expense_data.get("observation") or None,
        "month_ref": month_date,
    }

    response = (
        client.table("expenses")
        .insert(payload)
        .select("*, category:categories(*)")
        .execute()
    )
    rows = response.data if hasattr(response, "data") and response.data else []
    if not rows:
        raise RuntimeError("Falha ao inserir despesa no banco de dados.")
    return rows[0]


def update_expense(expense_id: str, patch: dict[str, Any], client: Any = None) -> dict[str, Any]:
    """
    Atualiza os campos de uma despesa existente (AC-008).
    """
    if client is None:
        client = get_client()

    payload = dict(patch)
    if "month_ref" in payload and payload["month_ref"]:
        payload["month_ref"] = month_ref_to_date(payload["month_ref"])

    response = (
        client.table("expenses")
        .update(payload)
        .eq("id", expense_id)
        .select("*, category:categories(*)")
        .execute()
    )
    rows = response.data if hasattr(response, "data") and response.data else []
    if not rows:
        raise RuntimeError(f"Despesa com ID {expense_id} não encontrada para atualização.")
    return rows[0]


def delete_expense(expense_id: str, client: Any = None) -> bool:
    """
    Exclui uma despesa do banco de dados (AC-008).
    """
    if client is None:
        client = get_client()

    response = client.table("expenses").delete().eq("id", expense_id).execute()
    return bool(hasattr(response, "data"))


def delete_expenses_batch(expense_ids: list[str], client: Any = None) -> bool:
    """
    Exclui múltiplas despesas do banco de dados em lote.
    """
    if not expense_ids:
        return True
    if client is None:
        client = get_client()

    response = client.table("expenses").delete().in_("id", expense_ids).execute()
    return bool(hasattr(response, "data"))


def toggle_expense_status(
    expense_id: str,
    current_status: str,
    client: Any = None,
) -> dict[str, Any]:
    """
    Alterna o status entre 'pendente' e 'pago' (AC-009).
    Quando passa para 'pago', preenche payment_date com a data atual (ISO YYYY-MM-DD).
    Quando passa para 'pendente', define payment_date como None.
    """
    if current_status == "pendente":
        new_status = "pago"
        new_payment_date = datetime.now().strftime("%Y-%m-%d")
    else:
        new_status = "pendente"
        new_payment_date = None

    return update_expense(
        expense_id=expense_id,
        patch={
            "status": new_status,
            "payment_date": new_payment_date,
        },
        client=client,
    )


def get_previous_month_ref(month_ref: str) -> str:
    """Retorna o mês anterior no formato AAAA-MM."""
    parts = month_ref[:7].split("-")
    y = int(parts[0])
    m = int(parts[1])
    m -= 1
    if m < 1:
        m = 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def get_previous_month_pending(month_ref: str, client: Any = None) -> dict[str, Any]:
    """
    Retorna as despesas pendentes do mês anterior e o resumo com total e quantidade.
    """
    if client is None:
        client = get_client()

    prev_month = get_previous_month_ref(month_ref)
    prev_month_date = month_ref_to_date(prev_month)

    try:
        response = (
            client.table("expenses")
            .select("*, category:categories(*)")
            .eq("month_ref", prev_month_date)
            .eq("status", "pendente")
            .order("due_date", desc=False)
            .execute()
        )
        items = response.data if hasattr(response, "data") and response.data else []
    except Exception:
        items = []

    total_amount = sum(float(item.get("amount") or 0.0) for item in items)
    return {
        "prev_month_ref": prev_month,
        "items": items,
        "count": len(items),
        "total_amount": total_amount,
    }

