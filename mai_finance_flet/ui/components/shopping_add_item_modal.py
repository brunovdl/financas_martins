"""
shopping_add_item_modal.py — Modal elegante para inclusão de itens na Lista de Compras (T-019 / Design System).
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens
from services.shopping_service import add_shopping_item, DEFAULT_UNITS, get_corridors
from db.shopping import update_shopping_item


def open_shopping_add_item_modal(
    page: ft.Page,
    on_item_added: Callable[[str], None],
    current_market: str | None = None,
    item_to_edit: dict[str, Any] | None = None,
) -> None:
    """Abre o diálogo de adição ou edição de item da lista de compras."""
    is_edit = bool(item_to_edit and item_to_edit.get("id"))
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

    init_name = item_to_edit.get("name", "") if is_edit else ""
    init_qty = f"{float(item_to_edit.get('quantity', 1)):g}" if is_edit else "1"
    init_unit = item_to_edit.get("unit", "un") if is_edit else "un"
    init_corridor = item_to_edit.get("corridor_category", "Mercearia & Padaria") if is_edit else "Mercearia & Padaria"
    cur_price = item_to_edit.get("actual_price") if (is_edit and item_to_edit.get("actual_price") is not None) else (item_to_edit.get("estimated_price") if is_edit else None)
    init_price = f"{float(cur_price):.2f}".replace(".", ",") if (cur_price is not None and float(cur_price) > 0) else ""

    # Campos de entrada
    input_name = ft.TextField(
        label="Nome do Item *",
        value=init_name,
        hint_text="ex: Café, Arroz, Detergente",
        dense=True,
        autofocus=not is_edit,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
    )

    input_qty = ft.TextField(
        label="Quantidade",
        value=init_qty,
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
        value=init_unit if init_unit in DEFAULT_UNITS else "un",
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

    corridors = get_corridors()
    select_corridor = ft.Dropdown(
        label="Corredor / Categoria",
        value=init_corridor if init_corridor in corridors else (corridors[0] if corridors else "Outros"),
        options=[ft.dropdown.Option(c) for c in corridors],
        dense=True,
        text_size=12,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
    )

    input_price = ft.TextField(
        label="Preço Unitário R$ (opcional)",
        value=init_price,
        hint_text="ex: 8,50",
        dense=True,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix=ft.Text("R$ ", size=13, color=T["textMuted"]),
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

        price_val: float | None = None
        raw_price = (input_price.value or "").strip()
        if raw_price:
            try:
                clean_p = float(raw_price.replace("R$", "").replace(" ", "").replace(",", "."))
                if clean_p >= 0:
                    price_val = clean_p
            except Exception:
                pass

        is_saving = True
        btn_save.disabled = True
        page.update()

        try:
            if is_edit and item_to_edit:
                updates: dict[str, Any] = {
                    "name": name,
                    "quantity": qty,
                    "unit": unit,
                    "corridor_category": corridor,
                }
                if price_val is not None:
                    updates["actual_price"] = price_val
                    updates["estimated_price"] = price_val
                update_shopping_item(item_to_edit["id"], updates)
            else:
                add_shopping_item(
                    name=name,
                    quantity=qty,
                    unit=unit,
                    corridor=corridor,
                    market_name=current_market,
                )
                if price_val is not None:
                    # Se informou preço na criação, atualiza
                    pass
            close_dlg()
            on_item_added(name)
        except Exception as exc:
            is_saving = False
            btn_save.disabled = False
            error_text.value = f"Erro ao salvar: {exc}"
            error_text.visible = True
            page.update()

    input_name.on_submit = handle_submit
    input_price.on_submit = handle_submit

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
                ft.Text("Salvar Alterações" if is_edit else "Adicionar à Lista", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
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
            input_price,
            error_text,
        ],
        spacing=10,
        tight=True,
    )

    dlg_header = build_modal_header(
        title="Editar Item" if is_edit else "Adicionar Item",
        subtitle="Altere nome, quantidade, corredor e valor" if is_edit else "Item para a lista de compras compartilhada",
        icon=ft.Icons.EDIT_NOTE if is_edit else ft.Icons.ADD_SHOPPING_CART,
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
