"""
shopping_item_card.py — Card visual de item da lista de compras compatível com Design System (T-019).

Implementa:
- Layout em 2 linhas anti-encavalamento (DEC-030)
- Visual adaptativo Dark/Light (get_tokens)
- Alvo de toque amplo (mínimo 48px) para mobile (AC-026)
- Exibição de quantidade, unidade e preço cotado
- Botões de ação (câmera, editar, excluir) alinhados à direita
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.theme import get_tokens, format_brl


def build_shopping_item_card(
    item: dict[str, Any],
    theme_mode: str,
    on_delete: Callable[[str], None] | None = None,
    on_toggle: Callable[[str, bool], None] | None = None,
    on_edit: Callable[[dict[str, Any]], None] | None = None,
    on_scan_price: Callable[[dict[str, Any]], None] | None = None,
    is_market_mode: bool = False,
) -> ft.Container:
    """Gera o card de um item da lista de compras com layout de 2 linhas anti-encavalamento."""
    T = get_tokens(theme_mode)
    item_id = str(item.get("id", ""))
    is_bought = bool(item.get("is_bought", False))
    name = item.get("name", "")
    quantity = float(item.get("quantity", 1.0) or 1.0)
    unit = item.get("unit", "un")
    est_price = float(item.get("estimated_price", 0.0) or 0.0)
    act_price = float(item["actual_price"]) if item.get("actual_price") is not None else None
    unit_price = act_price if act_price is not None else est_price
    total_price = unit_price * quantity if unit_price > 0 else 0.0

    # --- Linha 1: Checkbox + Nome do produto (expand total) ---
    text_color = T["textMuted"] if is_bought else T["textPrimary"]
    text_style = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if is_bought else None

    title_text = ft.Text(
        name,
        size=14,
        weight=ft.FontWeight.W_600,
        color=text_color,
        style=text_style,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )

    row1_controls: list[ft.Control] = []

    if on_toggle:
        if is_market_mode:
            check_icon = ft.Icons.CHECK_CIRCLE if is_bought else ft.Icons.RADIO_BUTTON_UNCHECKED
            check_color = T["success"] if is_bought else T["textMuted"]
            check_size = 26
        else:
            check_icon = ft.Icons.CHECK_BOX if is_bought else ft.Icons.CHECK_BOX_OUTLINE_BLANK
            check_color = T["accent"] if is_bought else T["textMuted"]
            check_size = 20

        btn_check = ft.IconButton(
            icon=check_icon,
            icon_color=check_color,
            icon_size=check_size,
            tooltip="Desmarcar item" if is_bought else "Marcar como comprado",
            on_click=lambda _: on_toggle(item_id, not is_bought),
        )
        row1_controls.append(btn_check)

    row1_controls.append(title_text)

    row1 = ft.Row(
        row1_controls,
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- Linha 2: Quantidade + Preço à esquerda | Ações à direita ---
    qty_text = ft.Text(
        f"{quantity:g} {unit}",
        size=12,
        color=T["textMuted"] if is_bought else T["accent"],
        weight=ft.FontWeight.BOLD,
    )

    price_str = format_brl(total_price) if total_price > 0 else "Sem cotação"
    price_text = ft.Text(
        price_str,
        size=12,
        color=T["textMuted"] if is_bought else (T["success"] if total_price > 0 else T["textMuted"]),
        weight=ft.FontWeight.W_500,
    )

    info_left = ft.Row(
        [qty_text, ft.Text("•", size=10, color=T["borderSubtle"]), price_text],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    actions_row: list[ft.Control] = []

    if on_scan_price:
        btn_scan = ft.IconButton(
            icon=ft.Icons.DOCUMENT_SCANNER_OUTLINED if is_market_mode else ft.Icons.CAMERA_ALT_OUTLINED,
            icon_size=18,
            icon_color=T["accent"],
            tooltip="Escanear etiqueta de preço",
            on_click=lambda _: on_scan_price(item),
        )
        actions_row.append(btn_scan)

    if not is_market_mode and on_edit:
        btn_edit = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=17,
            icon_color=T["textMuted"],
            tooltip="Editar item",
            on_click=lambda _: on_edit(item),
        )
        actions_row.append(btn_edit)

    if not is_market_mode and on_delete:
        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=17,
            icon_color=T["danger"],
            tooltip="Excluir item",
            on_click=lambda _: on_delete(item_id),
        )
        actions_row.append(btn_delete)

    row2_controls: list[ft.Control] = [info_left]
    if actions_row:
        row2_controls.append(ft.Row(actions_row, spacing=0, tight=True))

    row2 = ft.Row(
        row2_controls,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    card_bg = T["surfaceSolid"] if theme_mode == "dark" else "#FFFFFF"
    card_border = T["accent"] if is_bought and is_market_mode else T["borderSubtle"]

    return ft.Container(
        content=ft.Column([row1, row2], spacing=2),
        bgcolor=card_bg,
        border=ft.Border.all(1, card_border),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=8, vertical=6) if on_toggle else ft.Padding.symmetric(horizontal=12, vertical=10),
        margin=ft.Margin.only(bottom=6),
        on_click=lambda _: on_edit(item) if on_edit else None,
        tooltip="Toque para editar o item" if on_edit else None,
    )
