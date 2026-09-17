"""
clone_month.py — Serviço de clonagem de despesas entre meses.

Implementa:
- Clonagem de despesas de um mês de origem para um mês de destino (AC-012)
- Ajuste inteligente de data de vencimento (due_date) para o mesmo dia no mês destino
- Truncamento/clamp para o último dia do mês quando o dia de vencimento não existe (ex: 31 Jan -> 28/29 Fev)
- Reset de status para 'pendente' e payment_date para None (AC-012)
- Atribuição do month_ref de destino no formato AAAA-MM-01
"""
from __future__ import annotations

import calendar
from typing import Any
from db.supabase_client import get_client
from services.expenses import list_expenses, month_ref_to_date


def calculate_cloned_due_date(original_due_date: str, target_month_ref: str) -> str:
    """
    Calcula a nova data de vencimento no mês destino, mantendo o mesmo dia.
    Se o dia não existir no mês destino (ex.: dia 31 em fevereiro ou abril),
    ajusta para o último dia válido daquele mês.
    """
    # Extrai o dia original (ISO AAAA-MM-DD)
    day_str = original_due_date.split("-")[-1]
    original_day = int(day_str)

    # Extrai ano e mês do mês destino (AAAA-MM)
    target_clean = target_month_ref[:7]
    parts = target_clean.split("-")
    target_year = int(parts[0])
    target_month = int(parts[1])

    max_days = calendar.monthrange(target_year, target_month)[1]
    clamped_day = min(original_day, max_days)

    return f"{target_year:04d}-{target_month:02d}-{clamped_day:02d}"


def clone_month(source_month: str, target_month: str, client: Any = None) -> list[dict[str, Any]]:
    """
    Clona todas as despesas do mês de origem para o mês de destino (AC-012).
    """
    if client is None:
        client = get_client()

    clean_source = source_month[:7]
    clean_target = target_month[:7]

    if clean_source == clean_target:
        raise ValueError("O mês de origem e destino devem ser diferentes.")

    # 1. Busca despesas do mês de origem
    source_expenses = list_expenses(clean_source, client=client)
    if not source_expenses:
        return []

    target_month_date = month_ref_to_date(clean_target)

    # 2. Monta o payload clonado com regras do AC-012
    payloads = []
    for exp in source_expenses:
        new_due = calculate_cloned_due_date(str(exp["due_date"]), clean_target)
        payload = {
            "description": exp.get("description") or "",
            "amount": float(exp.get("amount") or 0.0),
            "due_date": new_due,
            "category_id": exp.get("category_id") or None,
            "status": "pendente",       # AC-012: reset para pendente
            "payment_date": None,       # AC-012: payment_date nulo
            "observation": exp.get("observation") or None,
            "month_ref": target_month_date,
        }
        payloads.append(payload)

    # 3. Insere no Supabase
    response = (
        client.table("expenses")
        .insert(payloads)
        .select("*, category:categories(*)")
        .execute()
    )
    return response.data if hasattr(response, "data") and response.data else []
