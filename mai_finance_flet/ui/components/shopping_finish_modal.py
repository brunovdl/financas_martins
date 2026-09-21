"""
shopping_finish_modal.py — Modal de finalização de compra e geração de despesa (T-020).

Implementa:
- Resumo dos itens comprados no caixa (AC-029)
- Ajuste e confirmação do valor real do cupom fiscal
- Criação automática da despesa no MAI Finance
- Arquivamento da compra no histórico e limpeza da lista semanal
- Fechamento determinístico padrão Gold Standard
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
import flet as ft

from services.categories import list_categories
from services.expenses import create_expense, month_ref_to_date
from db.shopping import save_shopping_history, clear_bought_items
from ui.components.modal_header import build_modal_header
from ui.components.mai_loading import MaiLoading
from ui.theme import get_tokens, format_brl, get_current_month_ref


def open_shopping_finish_modal(
    page: ft.Page,
    bought_items: list[dict[str, Any]],
    market_name: str | None,
    total_calculated: float,
    on_completed: Callable[[], None],
) -> None:
    """Abre modal para conferência do cupom fiscal e registro automático da despesa."""
    theme_mode = getattr(page, "theme_mode", ft.ThemeMode.DARK)
    mode_str = "light" if theme_mode == ft.ThemeMode.LIGHT else "dark"
    T = get_tokens(mode_str)

    dlg = ft.AlertDialog(modal=True)

    def close_dlg(_: Any = None) -> None:
        dlg.open = False
        if hasattr(page, "pop_dialog"):
            try:
                page.pop_dialog()
            except Exception:
                pass
        page.update()

    # Tenta buscar categoria Mercado ou Alimentação
    categories = []
    default_cat_id = None
    try:
        categories = list_categories()
        for c in categories:
            c_name = c.get("name", "").lower()
            if "mercado" in c_name or "alimenta" in c_name:
                default_cat_id = c.get("id")
                break
        if not default_cat_id and categories:
            default_cat_id = categories[0].get("id")
    except Exception:
        pass

    input_receipt = ft.TextField(
        value=f"{total_calculated:.2f}".replace(".", ","),
        label="Valor Real do Cupom Fiscal (R$)",
        hint_text="Ex: 245,80",
        dense=True,
        text_size=14,
        border_radius=8,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        color=T["textPrimary"],
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix=ft.Text("R$ ", color=T["textMuted"], size=13),
    )

    cat_options = [
        ft.dropdown.Option(key=str(c["id"]), text=c.get("name", "Geral"))
        for c in categories
    ]
    if not cat_options:
        cat_options = [ft.dropdown.Option(key="none", text="Alimentação / Mercado")]

    select_category = ft.Dropdown(
        value=str(default_cat_id) if default_cat_id else (cat_options[0].key if cat_options else None),
        options=cat_options,
        label="Categoria da Despesa",
        dense=True,
        text_size=13,
        border_radius=8,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        color=T["textPrimary"],
    )

    btn_confirm = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                ft.Text("Confirmar e Gerar Despesa", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        style=ft.ButtonStyle(
            bgcolor=T["accent"],
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ),
        height=38,
    )

    def handle_submit(_: Any) -> None:
        btn_confirm.disabled = True
        btn_confirm.content = MaiLoading.button_spinner("Registrando...")
        page.update()

        # Parse do valor do cupom
        raw_val = input_receipt.value.strip().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            final_amount = float(raw_val)
        except Exception:
            final_amount = float(total_calculated)

        today_iso = datetime.now().strftime("%Y-%m-%d")
        current_m_ref = get_current_month_ref()

        cat_id = select_category.value if select_category.value != "none" else None

        desc = f"Mercado - {market_name}" if market_name else "Supermercado (Lista de Compras)"

        expense_id = None
        try:
            expense_record = create_expense({
                "description": desc,
                "amount": final_amount,
                "due_date": today_iso,
                "payment_date": today_iso,
                "status": "pago",
                "category_id": cat_id,
                "month_ref": current_m_ref,
                "observation": f"Compra de {len(bought_items)} itens via Lista de Compras Inteligente.",
            })
            expense_id = expense_record.get("id")
        except Exception as exp_exc:
            print(f"[shopping_finish_modal] Erro ao criar despesa: {exp_exc}")

        # Arquiva histórico
        try:
            save_shopping_history(
                total_amount=final_amount,
                market_name=market_name,
                items_count=len(bought_items),
                items_snapshot=bought_items,
                expense_id=expense_id,
            )
        except Exception as hist_exc:
            print(f"[shopping_finish_modal] Erro ao salvar histórico: {hist_exc}")

        # Limpa os itens comprados da lista semanal
        try:
            clear_bought_items()
        except Exception as clr_exc:
            print(f"[shopping_finish_modal] Erro ao limpar itens: {clr_exc}")

        # Fechamento determinístico
        close_dlg()
        on_completed()

    btn_confirm.on_click = handle_submit

    dlg_header = build_modal_header(
        title="Finalizar Compra no Caixa",
        on_close=close_dlg,
        theme_tokens=T,
    )

    info_box = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Supermercado:", size=12, color=T["textMuted"]),
                        ft.Text(market_name or "Geral", size=12, weight=ft.FontWeight.BOLD, color=T["accent"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text("Itens Comprados:", size=12, color=T["textMuted"]),
                        ft.Text(f"{len(bought_items)} item(s)", size=12, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text("Total Calculado:", size=12, color=T["textMuted"]),
                        ft.Text(format_brl(total_calculated), size=13, weight=ft.FontWeight.BOLD, color=T["success"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=4,
        ),
        bgcolor=T["surfaceSolid"] if mode_str == "dark" else "#F8FAFC",
        border=ft.Border.all(1, T["borderSubtle"]),
        border_radius=8,
        padding=ft.Padding.all(10),
    )

    dlg_content = ft.Container(
        content=ft.Column(
            [
                info_box,
                ft.Container(height=6),
                input_receipt,
                ft.Container(height=4),
                select_category,
                ft.Container(height=8),
                btn_confirm,
            ],
            tight=True,
            spacing=6,
        ),
        width=380,
        padding=ft.Padding.all(14),
        bgcolor=T["surface"],
        border_radius=12,
    )

    dlg.title = dlg_header
    dlg.content = dlg_content
    dlg.actions = [
        ft.Button(
            content=ft.Text("Cancelar", color=T["textMuted"], size=12),
            on_click=close_dlg,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
    ]
    dlg.bgcolor = T["surface"]
    dlg.shape = ft.RoundedRectangleBorder(radius=12)

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()
