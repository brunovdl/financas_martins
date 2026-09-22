"""
market_quote_modal.py — Modal de cotação comparativa com abas de mercados e seletor de marcas (T-019).

Implementa:
- Abas/cartões expansíveis para 3 mercados reais da região (DEC-028)
- Chips interativos de marcas e preços por item com recálculo dinâmico do total (DEC-027)
- Gold Standard de modais do Design System (cabeçalho oficial, fechamento determinístico)
- API validada via flet-mcp: Tabs(length, selected_index, on_change, content), Tab(label, icon)
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
    """Abre o diálogo de cotação comparativa com abas de mercados e seletor de marcas."""
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
    best_market_name = quote_data.get("best_option")
    location = quote_data.get("location", {})
    city_label = location.get("city", "São Paulo")

    if not markets:
        close_dlg()
        return

    # Estado mutável de seleção de marcas e totais por mercado
    market_states: list[dict[str, Any]] = []
    for m in markets:
        items_state = []
        for it in m.get("items", []):
            brand_options = it.get("brand_options", [])
            selected_idx = 0
            # Encontrar o índice da marca pré-selecionada
            for i, opt in enumerate(brand_options):
                if opt.get("brand") == it.get("brand"):
                    selected_idx = i
                    break
            items_state.append({
                "data": dict(it),
                "brand_options": brand_options,
                "selected_idx": selected_idx,
            })
        market_states.append({
            "name": m.get("market_name", ""),
            "badge": m.get("badge", ""),
            "items": items_state,
            "total": float(m.get("total_amount", 0.0)),
        })

    def _recalculate_total(market_idx: int) -> float:
        """Recalcula o total do carrinho para um mercado baseado nas marcas selecionadas."""
        state = market_states[market_idx]
        total = 0.0
        for it_state in state["items"]:
            qty = float(it_state["data"].get("quantity", 1.0) or 1.0)
            options = it_state["brand_options"]
            sel_idx = it_state["selected_idx"]
            if options and 0 <= sel_idx < len(options):
                price = float(options[sel_idx].get("price", 0))
            else:
                price = float(it_state["data"].get("unit_price", 0))
            total += price * qty
        state["total"] = round(total, 2)
        return state["total"]

    # Referências para atualização dinâmica
    total_labels: list[ft.Text] = []
    items_columns: list[ft.Column] = []

    def _build_market_tab_content(market_idx: int) -> ft.Container:
        """Constrói o conteúdo de uma aba de mercado com itens e chips de marcas."""
        state = market_states[market_idx]
        m_name = state["name"]
        is_best = (m_name == best_market_name)

        item_controls: list[ft.Control] = []
        item_bg = T["surface"] if mode_str == "dark" else "#F8FAFC"

        for it_idx, it_state in enumerate(state["items"]):
            it_data = it_state["data"]
            it_name = it_data.get("name", "")
            qty = float(it_data.get("quantity", 1.0) or 1.0)
            unit = it_data.get("unit", "un")
            options = it_state["brand_options"]
            sel_idx = it_state["selected_idx"]

            if options and 0 <= sel_idx < len(options):
                current_price = float(options[sel_idx].get("price", 0))
                current_brand = options[sel_idx].get("brand", "")
            else:
                current_price = float(it_data.get("unit_price", 0))
                current_brand = it_data.get("brand", "")

            item_total = round(current_price * qty, 2)

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
                    on_click=lambda _, mi=market_idx, ii=it_idx, oi=opt_idx: _on_brand_chip_click(mi, ii, oi),
                    tooltip=opt.get("product_title", ""),
                )
                brand_chips.append(chip)

            price_label = ft.Text(
                format_brl(item_total),
                size=13,
                weight=ft.FontWeight.BOLD,
                color=T["textPrimary"],
            )

            item_row = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(it_name, size=13, weight=ft.FontWeight.BOLD, color=T["textPrimary"], expand=True),
                                price_label,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [
                                ft.Text(f"{qty:g} {unit}", size=11, color=T["textMuted"]),
                            ],
                            spacing=4,
                        ),
                        ft.Row(
                            brand_chips,
                            spacing=4,
                            wrap=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor=item_bg,
                border=ft.Border.all(1, T["borderSubtle"]),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            )
            item_controls.append(item_row)

        items_col = ft.Column(item_controls, spacing=6, scroll=ft.ScrollMode.AUTO)
        items_columns.append(items_col)

        total_text = ft.Text(
            format_brl(state["total"]),
            size=18,
            weight=ft.FontWeight.BOLD,
            color=T["success"] if is_best else T["textPrimary"],
        )
        total_labels.append(total_text)

        btn_apply = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                    ft.Text("Aplicar Preços à Lista", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            ),
            height=38,
            on_click=lambda _, mi=market_idx: _handle_apply(mi),
        )

        badge_label = "MELHOR OPÇÃO" if is_best else state["badge"]
        badge_bg = T["accent"] if is_best else T["surface"]
        badge_text_color = "#08090F" if is_best else T["accent"]

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.STOREFRONT, size=20, color=T["accent"]),
                            ft.Text(m_name, size=14, weight=ft.FontWeight.BOLD, color=T["textPrimary"], expand=True),
                            ft.Container(
                                content=ft.Text(badge_label, size=9, weight=ft.FontWeight.BOLD, color=badge_text_color),
                                bgcolor=badge_bg,
                                border=ft.Border.all(1, T["accent"]),
                                border_radius=4,
                                padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color=T["borderSubtle"]),
                    ft.Container(content=items_col, height=min(len(state["items"]) * 88, 260)),
                    ft.Divider(height=1, color=T["borderSubtle"]),
                    ft.Row(
                        [
                            ft.Text("Total Estimado:", size=13, color=T["textMuted"]),
                            total_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    btn_apply,
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.Padding.all(8),
        )

    def _on_brand_chip_click(market_idx: int, item_idx: int, option_idx: int) -> None:
        """Atualiza a marca selecionada de um item e recalcula o total do mercado."""
        market_states[market_idx]["items"][item_idx]["selected_idx"] = option_idx
        new_total = _recalculate_total(market_idx)

        # Atualiza label do total
        if market_idx < len(total_labels):
            total_labels[market_idx].value = format_brl(new_total)

        # Re-renderiza os itens do mercado ativo
        _rebuild_market_items(market_idx)
        page.update()

    def _rebuild_market_items(market_idx: int) -> None:
        """Re-renderiza os chips de marcas de um mercado após troca de seleção."""
        if market_idx >= len(items_columns):
            return
        state = market_states[market_idx]
        items_col = items_columns[market_idx]
        item_bg = T["surface"] if mode_str == "dark" else "#F8FAFC"

        new_controls: list[ft.Control] = []
        for it_idx, it_state in enumerate(state["items"]):
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

            brand_chips = []
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
                    on_click=lambda _, mi=market_idx, ii=it_idx, oi=opt_idx: _on_brand_chip_click(mi, ii, oi),
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
                        ft.Row([ft.Text(f"{qty:g} {unit}", size=11, color=T["textMuted"])], spacing=4),
                        ft.Row(brand_chips, spacing=4, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor=item_bg,
                border=ft.Border.all(1, T["borderSubtle"]),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            )
            new_controls.append(item_row)

        items_col.controls = new_controls

    def _handle_apply(market_idx: int) -> None:
        """Aplica as marcas selecionadas à lista de compras."""
        state = market_states[market_idx]
        m_name = state["name"]
        applied_items: list[dict[str, Any]] = []
        for it_state in state["items"]:
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
        on_market_selected(m_name, applied_items)

    # Construção do conteúdo das abas de cada mercado
    tab_contents: list[ft.Container] = []
    for idx, _ in enumerate(markets):
        content = _build_market_tab_content(idx)
        tab_contents.append(content)

    # Container para conteúdo ativo do mercado selecionado
    active_content = ft.Container(content=tab_contents[0] if tab_contents else ft.Container())

    dlg_header = build_modal_header(
        title="Cotação com IA nos Mercados",
        on_close=close_dlg,
        theme_tokens=T,
    )

    tab_bar = ft.Row(
        [
            ft.Container(
                content=ft.Text(
                    market_states[idx]["name"],
                    size=11,
                    weight=ft.FontWeight.BOLD if idx == 0 else ft.FontWeight.W_500,
                    color=T["accent"] if idx == 0 else T["textMuted"],
                ),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                border=ft.Border.only(bottom=ft.BorderSide(2, T["accent"] if idx == 0 else ft.Colors.TRANSPARENT)),
                on_click=lambda _, i=idx: _switch_tab(i),
            )
            for idx in range(len(market_states))
        ],
        spacing=2,
        scroll=ft.ScrollMode.AUTO,
    )

    _active_tab_idx = {"value": 0}

    def _switch_tab(idx: int) -> None:
        _active_tab_idx["value"] = idx
        if 0 <= idx < len(tab_contents):
            active_content.content = tab_contents[idx]
            # Atualizar estilos do tab bar
            for i, ctrl in enumerate(tab_bar.controls):
                ctrl.border = ft.Border.only(
                    bottom=ft.BorderSide(2, T["accent"] if i == idx else ft.Colors.TRANSPARENT)
                )
                text_ctrl = ctrl.content
                if hasattr(text_ctrl, "weight"):
                    text_ctrl.weight = ft.FontWeight.BOLD if i == idx else ft.FontWeight.W_500
                    text_ctrl.color = T["accent"] if i == idx else T["textMuted"]
            page.update()

    dlg_content = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"Comparativo para sua lista na região de {city_label}:",
                    size=12,
                    color=T["textMuted"],
                ),
                tab_bar,
                active_content,
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
