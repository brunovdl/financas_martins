"""
shopping_add_item_modal.py — Modal elegante para inclusão de itens na Lista de Compras (T-019 / Design System).
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens
from services.shopping_service import add_shopping_item, DEFAULT_UNITS, get_corridors


def open_shopping_add_item_modal(
    page: ft.Page,
    on_item_added: Callable[[str], None],
    current_market: str | None = None,
) -> None:
    """Abre o diálogo de adição de item à lista de compras."""
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

    # Campos de entrada
    input_name = ft.TextField(
        label="Nome do Item *",
        hint_text="ex: Café, Arroz, Detergente",
        dense=True,
        autofocus=True,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
    )

    input_qty = ft.TextField(
        label="Quantidade",
        value="1",
        dense=True,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=1,
    )

    select_unit = ft.Dropdown(
        label="Unidade",
        value="un",
        options=[ft.dropdown.Option(u) for u in DEFAULT_UNITS],
        dense=True,
        text_size=12,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
        expand=1,
    )

    select_corridor = ft.Dropdown(
        label="Corredor / Categoria",
        value="Mercearia & Padaria",
        options=[ft.dropdown.Option(c) for c in get_corridors()],
        dense=True,
        text_size=12,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
    )

    error_text = ft.Text("", size=11, color=T["danger"], visible=False)

    is_saving = False

    def handle_submit(_: Any = None) -> None:
        nonlocal is_saving
        if is_saving:
            return

        name = input_name.value.strip()
        if not name:
            error_text.value = "Por favor, digite o nome do item."
            error_text.visible = True
            page.update()
            return

        try:
            qty = float(input_qty.value.replace(",", "."))
            if qty <= 0:
                qty = 1.0
        except Exception:
            qty = 1.0

        unit = select_unit.value or "un"
        corridor = select_corridor.value or "Outros"

        is_saving = True
        btn_save.disabled = True
        page.update()

        try:
            add_shopping_item(
                name=name,
                quantity=qty,
                unit=unit,
                corridor=corridor,
                market_name=current_market,
            )
            close_dlg()
            on_item_added(name)
        except Exception as exc:
            is_saving = False
            btn_save.disabled = False
            error_text.value = f"Erro ao adicionar: {exc}"
            error_text.visible = True
            page.update()

    input_name.on_submit = handle_submit

    btn_cancel = ft.Button(
        content=ft.Text("Cancelar", size=12, color=T["textMuted"]),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ),
        height=38,
        on_click=close_dlg,
    )

    btn_save = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                ft.Text("Adicionar à Lista", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=T["accent"],
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ),
        height=38,
        on_click=handle_submit,
    )

    qty_unit_row = ft.Row([input_qty, select_unit], spacing=8)

    content_col = ft.Column(
        [
            input_name,
            qty_unit_row,
            select_corridor,
            error_text,
        ],
        spacing=10,
        tight=True,
    )

    dlg_header = build_modal_header(
        title="Adicionar Item",
        subtitle="Item para a lista de compras compartilhada",
        icon=ft.Icons.ADD_SHOPPING_CART,
        on_close=close_dlg,
        theme_mode=mode_str,
    )

    dlg.title = dlg_header
    dlg.content = ft.Container(content=content_col, width=320, padding=ft.Padding.only(top=4))
    dlg.actions = [btn_cancel, btn_save]
    dlg.actions_alignment = ft.MainAxisAlignment.END
    dlg.bgcolor = T["surface"]

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()
