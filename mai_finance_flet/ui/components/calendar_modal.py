"""
calendar_modal.py — Seletor de calendário personalizado em pt-BR (MAI Finance Design System).

Substitui a digitação manual de datas por um calendário visual completo, elegante e responsivo:
- Totalmente em pt-BR ("Janeiro", "Fevereiro"..., "Dom", "Seg", "Ter"...)
- Navegação fluida de meses e anos
- Destaque do dia selecionado e indicador do dia atual ("Hoje")
- Seleção direta com 1 clique e fechamento determinístico
- Conformidade total com o Design System (tema claro/escuro, mini-logo, bordas suaves)
"""
from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Callable
import flet as ft

try:
    from ui.components.modal_header import build_modal_header
    from ui.theme import MONTH_NAMES, THEMES, br_to_iso_date, iso_to_br_date
except ModuleNotFoundError:
    from mai_finance_flet.ui.components.modal_header import build_modal_header
    from mai_finance_flet.ui.theme import MONTH_NAMES, THEMES, br_to_iso_date, iso_to_br_date

WEEKDAYS_BR = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]


def open_calendar_modal(
    page: ft.Page,
    initial_date: str | None = None,
    on_date_selected: Callable[[str, str], None] | None = None,
    theme_tokens: dict[str, str] | None = None,
    title: str = "Selecionar Data",
    on_dismiss_callback: Callable[[], None] | None = None,
    parent_dialog: ft.AlertDialog | None = None,
) -> ft.AlertDialog:
    """Abre um modal de calendário personalizado em pt-BR no padrão MAI Finance.

    Args:
        page: Instância atual da ft.Page.
        initial_date: Data inicial em formato ISO (AAAA-MM-DD) ou BR (DD/MM/AAAA).
        on_date_selected: Callback que recebe (iso_date: str, br_date: str).
        theme_tokens: Dicionário de tokens de design system (se None, usa tema dark).
        title: Título exibido no cabeçalho padronizado.
        on_dismiss_callback: Callback acionado ao fechar/cancelar sem selecionar.
        parent_dialog: Modal pai anterior que deve ser restaurado ao fechar/selecionar.
    """
    T = theme_tokens or THEMES["dark"]

    # Determina a data de referência inicial
    parsed_date: date | None = None
    if initial_date:
        iso_candidate = br_to_iso_date(str(initial_date).strip())
        try:
            parts = [int(p) for p in iso_candidate.split("-")]
            if len(parts) == 3:
                parsed_date = date(parts[0], parts[1], parts[2])
        except Exception:
            parsed_date = None

    today = datetime.now().date()
    ref_date = parsed_date or today

    current_state = {
        "year": ref_date.year,
        "month": ref_date.month,
        "selected": parsed_date,
    }

    month_label_text = ft.Text(
        "",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=T.get("textPrimary", "#EDF0F7"),
        text_align=ft.TextAlign.CENTER,
    )

    grid_column = ft.Column(spacing=4, tight=True)

    def close_dlg() -> None:
        if hasattr(page, "pop_dialog"):
            try:
                page.pop_dialog()
            except Exception:
                pass

        dlg.open = False
        try:
            dlg.update()
        except Exception:
            pass

        if parent_dialog is not None:
            parent_dialog.open = True
            try:
                parent_dialog.update()
            except Exception:
                pass

        try:
            page.update()
        except Exception:
            pass

    def cancel_action() -> None:
        close_dlg()
        if on_dismiss_callback:
            try:
                on_dismiss_callback()
            except Exception:
                pass

    def select_and_confirm(target_date: date) -> None:
        iso_str = target_date.strftime("%Y-%m-%d")
        br_str = target_date.strftime("%d/%m/%Y")
        if on_date_selected:
            try:
                on_date_selected(iso_str, br_str)
            except Exception:
                pass
        close_dlg()

    def render_calendar() -> None:
        y = current_state["year"]
        m = current_state["month"]
        month_label_text.value = f"{MONTH_NAMES[m - 1]} {y}"

        cal = calendar.Calendar(firstweekday=6)  # 6 = Domingo como primeiro dia
        weeks = cal.monthdayscalendar(y, m)

        grid_column.controls.clear()

        # Cabeçalho dos dias da semana
        header_cells = [
            ft.Container(
                content=ft.Text(wd, size=11, weight=ft.FontWeight.BOLD, color=T.get("textMuted", "#8891A8"), text_align=ft.TextAlign.CENTER),
                width=36,
                height=26,
                alignment=ft.Alignment.CENTER,
            )
            for wd in WEEKDAYS_BR
        ]
        grid_column.controls.append(ft.Row(header_cells, spacing=2, alignment=ft.MainAxisAlignment.CENTER))

        # Dias do mês
        for week in weeks:
            row_cells = []
            for day in week:
                if day == 0:
                    row_cells.append(ft.Container(width=36, height=36))
                else:
                    d_date = date(y, m, day)
                    is_selected = (current_state["selected"] == d_date)
                    is_today = (today == d_date)

                    if is_selected:
                        bg = T.get("accent", "#3FD6C4")
                        fg = T.get("accentOnBrand", "#08090F")
                        border = None
                        weight = ft.FontWeight.BOLD
                    elif is_today:
                        bg = T.get("surfaceSolid", "#151B2E")
                        fg = T.get("accent", "#3FD6C4")
                        border = ft.Border.all(1.5, T.get("accent", "#3FD6C4"))
                        weight = ft.FontWeight.BOLD
                    else:
                        bg = T.get("surfaceSolid", "#151B2E")
                        fg = T.get("textPrimary", "#EDF0F7")
                        border = ft.Border.all(1, T.get("borderSubtle", "#1B2138"))
                        weight = ft.FontWeight.NORMAL

                    cell = ft.Container(
                        content=ft.Text(str(day), size=12, weight=weight, color=fg, text_align=ft.TextAlign.CENTER),
                        width=36,
                        height=36,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=bg,
                        border=border,
                        border_radius=8,
                        ink=True,
                        tooltip=f"{day:02d}/{m:02d}/{y}",
                        on_click=lambda _, dt=d_date: select_and_confirm(dt),
                    )
                    row_cells.append(cell)
            grid_column.controls.append(ft.Row(row_cells, spacing=2, alignment=ft.MainAxisAlignment.CENTER))

        try:
            page.update()
        except Exception:
            pass

    def prev_month(_) -> None:
        if current_state["month"] == 1:
            current_state["month"] = 12
            current_state["year"] -= 1
        else:
            current_state["month"] -= 1
        render_calendar()

    def next_month(_) -> None:
        if current_state["month"] == 12:
            current_state["month"] = 1
            current_state["year"] += 1
        else:
            current_state["month"] += 1
        render_calendar()

    # Barra superior de navegação de mês/ano
    nav_row = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_size=20,
                icon_color=T.get("accent", "#3FD6C4"),
                tooltip="Mês anterior",
                on_click=prev_month,
            ),
            month_label_text,
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_size=20,
                icon_color=T.get("accent", "#3FD6C4"),
                tooltip="Próximo mês",
                on_click=next_month,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    btn_today = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.TODAY, size=15, color=T.get("accent", "#3FD6C4")),
                ft.Text("Hoje", size=12, weight=ft.FontWeight.W_600, color=T.get("accent", "#3FD6C4")),
            ],
            spacing=4,
            tight=True,
        ),
        style=ft.ButtonStyle(
            bgcolor=T.get("surfaceSolid", "#151B2E"),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=lambda _: select_and_confirm(today),
    )

    btn_cancel = ft.Button(
        content=ft.Text("Cancelar", size=12, color=T.get("textMuted", "#8891A8")),
        style=ft.ButtonStyle(
            bgcolor=T.get("surfaceSolid", "#151B2E"),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=lambda _: cancel_action(),
    )

    modal_header = build_modal_header(
        title=title,
        on_close=cancel_action,
        theme_tokens=T,
    )

    dlg_content = ft.Container(
        content=ft.Column(
            [
                nav_row,
                ft.Divider(height=1, color=T.get("borderSubtle", "#1B2138")),
                grid_column,
            ],
            spacing=8,
            tight=True,
        ),
        width=290,
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=modal_header,
        content=dlg_content,
        bgcolor=T.get("surface", "#121628"),
        shape=ft.RoundedRectangleBorder(radius=12),
        actions=[btn_today, btn_cancel],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    render_calendar()

    dlg.open = True
    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        try:
            page.update()
        except Exception:
            pass

    return dlg
