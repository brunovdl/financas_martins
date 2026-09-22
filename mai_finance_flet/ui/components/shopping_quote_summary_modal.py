"""
shopping_quote_summary_modal.py — Modal de resumo de cotação com seletor de marcas (T-019 / Design System).

Implementa (DEC-027):
- Cotação para mercado específico com chips interativos de marcas
- Recálculo dinâmico do total ao trocar a marca de um item
- Gold Standard de modais do Design System
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens, format_brl


def open_shopping_quote_summary_modal(
    page: ft.Page,
    market_name: str,
    city: str,
    quote_data: dict[str, Any],
    on_apply_prices: Callable[[str, list[dict[str, Any]]], None],
) -> None:
    """Exibe o resultado da cotação direcionada para um mercado específico com seletor de marcas."""
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

    markets = quote_data.get("markets", [])
    m_info = markets[0] if markets else {}
    items = m_info.get("items", [])

    # Estado mutável para seleção de marcas por item
    items_state: list[dict[str, Any]] = []
    for it in items:
        brand_options = it.get("brand_options", [])
        selected_idx = 0
        for i, opt in enumerate(brand_options):
            if opt.get("brand") == it.get("brand"):
                selected_idx = i
                break
        items_state.append({
            "data": dict(it),
            "brand_options": brand_options,
            "selected_idx": selected_idx,
        })

    total_ref = {"value": float(m_info.get("total_amount", 0.0))}

    def _recalculate_total() -> float:
        total = 0.0
        for it_state in items_state:
            qty = float(it_state["data"].get("quantity", 1.0) or 1.0)
            options = it_state["brand_options"]
            sel_idx = it_state["selected_idx"]
            if options and 0 <= sel_idx < len(options):
                price = float(options[sel_idx].get("price", 0))
            else:
                price = float(it_state["data"].get("unit_price", 0))
            total += price * qty
        total_ref["value"] = round(total, 2)
        return total_ref["value"]

    total_text = ft.Text(
        format_brl(total_ref["value"]),
        size=18,
        weight=ft.FontWeight.BOLD,
        color=T["success"],
    )

    items_col = ft.Column([], spacing=6, scroll=ft.ScrollMode.AUTO)

    def _build_item_rows() -> None:
        """Constrói/reconstrói os rows de itens com chips de marcas."""
        item_bg = T["surface"] if mode_str == "dark" else "#F8FAFC"
        new_controls: list[ft.Control] = []

        for it_idx, it_state in enumerate(items_state):
            it_data = it_state["data"]
            it_name = it_data.get("name", "")
            qty = float(it_data.get("quantity", 1.0) or 1.0)
            unit = it_data.get("unit", "un")
            options = it_state["brand_options"]
            sel_idx = it_state["selected_idx"]

            if options and 0 <= sel_idx < len(options):
                current_price = float(options[sel_idx].get("price", 0))
            else:
                current_price = float(it_data.get("unit_price", 0))
            item_total = round(current_price * qty, 2)

            price_subtext = f"{qty:g} {unit} × {format_brl(current_price)}" if qty > 1 else f"{qty:g} {unit}"

            # Chips de marcas
            brand_chips: list[ft.Control] = []
            for opt_idx, opt in enumerate(options):
                is_selected = (opt_idx == sel_idx)
                chip_bg = T["accent"] if is_selected else (T["surfaceSolid"] if mode_str == "dark" else "#EEF2F6")
                chip_text_color = "#08090F" if is_selected else T["textMuted"]

                chip = ft.Container(
                    content=ft.Text(
                        f"{opt.get('brand', '?')} {format_brl(float(opt.get('price', 0)))}",
                        size=10,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500,
                        color=chip_text_color,
                    ),
                    bgcolor=chip_bg,
                    border=ft.Border.all(1, T["accent"] if is_selected else T["borderSubtle"]),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    on_click=lambda _, ii=it_idx, oi=opt_idx: _on_brand_chip_click(ii, oi),
                    tooltip=opt.get("product_title", ""),
                )
                brand_chips.append(chip)

            item_row = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(it_name, size=13, weight=ft.FontWeight.BOLD, color=T["textPrimary"], expand=True),
                                ft.Text(format_brl(item_total), size=13, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(price_subtext, size=11, color=T["textMuted"]),
                        ft.Row(brand_chips, spacing=4, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER) if brand_chips else ft.Container(),
                    ],
                    spacing=3,
                    tight=True,
                ),
                bgcolor=item_bg,
                border=ft.Border.all(1, T["borderSubtle"]),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            )
            new_controls.append(item_row)

        items_col.controls = new_controls

    def _on_brand_chip_click(item_idx: int, option_idx: int) -> None:
        items_state[item_idx]["selected_idx"] = option_idx
        new_total = _recalculate_total()
        total_text.value = format_brl(new_total)
        _build_item_rows()
        page.update()

    _build_item_rows()

    def handle_apply(_: Any = None) -> None:
        applied_items: list[dict[str, Any]] = []
        for it_state in items_state:
            it_data = dict(it_state["data"])
            options = it_state["brand_options"]
            sel_idx = it_state["selected_idx"]
            if options and 0 <= sel_idx < len(options):
                opt = options[sel_idx]
                it_data["brand"] = opt.get("brand", it_data.get("brand", ""))
                it_data["unit_price"] = float(opt.get("price", it_data.get("unit_price", 0)))
                it_data["product_title"] = opt.get("product_title", it_data.get("product_title", ""))
                qty = float(it_data.get("quantity", 1.0) or 1.0)
                it_data["total_price"] = round(it_data["unit_price"] * qty, 2)
            applied_items.append(it_data)
        close_dlg()
        on_apply_prices(market_name, applied_items)

    list_height = min(len(items) * 80, 280) if items else 60

    summary_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.STOREFRONT, size=24, color=T["accent"]),
                        ft.Column(
                            [
                                ft.Text(market_name, size=15, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                                ft.Text(f"Região: {city}", size=11, color=T["textMuted"]),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Divider(color=T["borderSubtle"], height=12),
                ft.Row(
                    [
                        ft.Text("Itens Cotados com IA:", size=11, weight=ft.FontWeight.BOLD, color=T["textMuted"]),
                        ft.Text(f"{len(items)} itens", size=11, color=T["textMuted"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(content=items_col, height=list_height),
                ft.Divider(color=T["borderSubtle"], height=12),
                ft.Row(
                    [
                        ft.Text("Total Estimado:", size=13, color=T["textMuted"]),
                        total_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=6,
        ),
        bgcolor=T["surfaceSolid"] if mode_str == "dark" else "#FFFFFF",
        border=ft.Border.all(1, T["borderSubtle"]),
        border_radius=8,
        padding=ft.Padding.all(12),
    )

    btn_cancel = ft.Button(
        content=ft.Text("Fechar", size=12, color=T["textMuted"]),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ),
        height=38,
        on_click=close_dlg,
    )

    btn_apply = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color="#08090F"),
                ft.Text("Aplicar Preços à Lista", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
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
        on_click=handle_apply,
    )

    dlg_header = build_modal_header(
        title="Cotação Concluída",
        on_close=close_dlg,
        theme_tokens=T,
    )

    dlg.title = dlg_header
    dlg.content = ft.Container(content=summary_card, width=360, padding=ft.Padding.only(top=4))
    dlg.actions = [btn_cancel, btn_apply]
    dlg.actions_alignment = ft.MainAxisAlignment.END
    dlg.bgcolor = T["surface"]
    dlg.shape = ft.RoundedRectangleBorder(radius=12)

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()
