"""
shopping_quote_summary_modal.py — Modal de resumo de cotação para mercado específico (T-019 / Design System).
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
    """Exibe o resultado da cotação direcionada para um mercado específico."""
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
    total_amount = float(m_info.get("total_amount", 0.0))
    items = m_info.get("items", [])

    def handle_apply(_: Any = None) -> None:
        close_dlg()
        on_apply_prices(market_name, items)

    # Montagem da lista de itens cotados
    quoted_item_rows: list[ft.Control] = []
    item_bg = T["surface"] if mode_str == "dark" else "#F8FAFC"

    for it in items:
        it_name = it.get("name", "")
        brand = it.get("brand", "") or "Marca Selecionada"
        qty = float(it.get("quantity", 1.0) or 1.0)
        unit = it.get("unit", "un")
        u_price = float(it.get("unit_price", 0.0) or 0.0)
        t_price = float(it.get("total_price", 0.0) or (u_price * qty))

        price_subtext = f"{qty:g} {unit} × {format_brl(u_price)}" if qty > 1 else f"{qty:g} {unit}"

        item_row = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(it_name, size=13, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            f"Marca: {brand}",
                                            size=10,
                                            weight=ft.FontWeight.W_500,
                                            color=T["accent"],
                                        ),
                                        bgcolor=T["surfaceSolid"] if mode_str == "dark" else "#EEF2F6",
                                        border_radius=4,
                                        padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                                    ),
                                    ft.Text(price_subtext, size=11, color=T["textMuted"]),
                                ],
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Text(
                        format_brl(t_price),
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=T["textPrimary"],
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=item_bg,
            border=ft.Border.all(1, T["borderSubtle"]),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        )
        quoted_item_rows.append(item_row)

    list_height = min(len(items) * 58, 240) if items else 60
    items_scroll_box = ft.Container(
        content=ft.Column(
            quoted_item_rows,
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            height=list_height,
        ),
    )


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
                items_scroll_box,
                ft.Divider(color=T["borderSubtle"], height=12),
                ft.Row(
                    [
                        ft.Text("Total Estimado:", size=13, color=T["textMuted"]),
                        ft.Text(format_brl(total_amount), size=18, weight=ft.FontWeight.BOLD, color=T["success"]),
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
        subtitle=f"Preços cotados para {market_name}",
        icon=ft.Icons.AUTO_AWESOME,
        on_close=close_dlg,
        theme_mode=mode_str,
    )

    dlg.title = dlg_header
    dlg.content = ft.Container(content=summary_card, width=360, padding=ft.Padding.only(top=4))
    dlg.actions = [btn_cancel, btn_apply]
    dlg.actions_alignment = ft.MainAxisAlignment.END
    dlg.bgcolor = T["surface"]

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()
