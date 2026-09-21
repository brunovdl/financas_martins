"""
market_quote_modal.py — Modal de comparação e seleção de supermercado com IA (T-019).

Implementa:
- Gold Standard de modais do Design System (cabeçalho oficial, fechamento determinístico)
- Comparação do valor total do carrinho entre 2 ou 3 redes de supermercado (AC-024)
- Seleção de supermercado único para toda a compra
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens, format_brl


def open_market_quote_modal(
    page: ft.Page,
    quote_data: dict[str, Any],
    on_market_selected: Callable[[str, list[dict[str, Any]]], None],
) -> None:
    """Abre o diálogo de cotação comparativa de supermercados."""
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

    def handle_select_market(market_name: str, items: list[dict[str, Any]]) -> None:
        close_dlg()
        on_market_selected(market_name, items)

    markets = quote_data.get("markets", [])
    best_market_name = quote_data.get("best_option")
    location = quote_data.get("location", {})
    city_label = f"Região: {location.get('city', 'São Paulo')}"

    market_cards: list[ft.Control] = []

    for m in markets:
        m_name = m.get("market_name", "")
        m_total = float(m.get("total_amount", 0.0))
        m_badge = m.get("badge", "")
        m_items = m.get("items", [])
        is_best = (m_name == best_market_name)

        header_row = ft.Row(
            [
                ft.Text(m_name, size=15, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                ft.Container(
                    content=ft.Text(
                        "MELHOR OPÇÃO" if is_best else m_badge,
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color="#08090F" if is_best else T["accent"],
                    ),
                    bgcolor=T["accent"] if is_best else T["surface"],
                    border=ft.Border.all(1, T["accent"]),
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        total_row = ft.Row(
            [
                ft.Text("Total da Lista:", size=12, color=T["textMuted"]),
                ft.Text(format_brl(m_total), size=16, weight=ft.FontWeight.BOLD, color=T["success"] if is_best else T["textPrimary"]),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        btn_select = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                    ft.Text("Selecionar este Mercado", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            ),
            height=36,
            on_click=lambda _, name=m_name, its=m_items: handle_select_market(name, its),
        )

        card = ft.Container(
            content=ft.Column(
                [
                    header_row,
                    ft.Divider(height=1, color=T["borderSubtle"]),
                    total_row,
                    ft.Container(height=4),
                    btn_select,
                ],
                spacing=6,
            ),
            bgcolor=T["surfaceSolid"] if mode_str == "dark" else "#FFFFFF",
            border=ft.Border.all(1.5 if is_best else 1, T["accent"] if is_best else T["borderSubtle"]),
            border_radius=10,
            padding=ft.Padding.all(12),
            margin=ft.Margin.only(bottom=8),
        )
        market_cards.append(card)

    dlg_header = build_modal_header(
        title="Cotação com IA nos Mercados",
        on_close=close_dlg,
        theme_tokens=T,
    )

    dlg_content = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"Comparativo de preços nos sites oficiais para a sua lista ({city_label}):",
                    size=12,
                    color=T["textMuted"],
                ),
                ft.Container(height=6),
                ft.Column(market_cards, scroll=ft.ScrollMode.AUTO),
            ],
            tight=True,
            spacing=4,
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
            content=ft.Text("Fechar", color=T["textMuted"], size=12),
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
