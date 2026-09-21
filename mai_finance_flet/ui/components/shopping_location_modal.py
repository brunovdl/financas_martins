"""
shopping_location_modal.py — Modal para configuração de Cidade/UF e Supermercado (T-019 / Design System).
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from ui.components.modal_header import build_modal_header
from ui.theme import get_tokens
from ui.storage_util import set_local_item


def open_shopping_location_modal(
    page: ft.Page,
    current_city: str,
    current_market: str | None,
    on_location_saved: Callable[[str, str | None], None],
) -> None:
    """Abre diálogo para editar a Cidade e o Mercado de preferência para compras."""
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

    input_city = ft.TextField(
        label="Sua Cidade / UF *",
        value=current_city or "São Paulo, SP",
        hint_text="ex: Belo Horizonte, MG ou São Paulo, SP",
        dense=True,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
    )

    is_all_markets = not bool(current_market and current_market.strip())

    input_market = ft.TextField(
        label="Nome do Mercado Específico",
        value="" if is_all_markets else (current_market or ""),
        hint_text="ex: Carrefour, Supermercados BH, Atacadão",
        dense=True,
        text_size=13,
        bgcolor=T["surfaceSolid"],
        border_color=T["borderSubtle"],
        focused_border_color=T["accent"],
        color=T["textPrimary"],
        border_radius=8,
        visible=not is_all_markets,
    )

    def on_mode_change(e: Any) -> None:
        val = e.control.value
        input_market.visible = (val == "specific")
        page.update()

    radio_group = ft.RadioGroup(
        content=ft.Column(
            [
                ft.Radio(
                    value="all",
                    label="Principais mercados da cidade",
                    label_style=ft.TextStyle(size=13, color=T["textPrimary"]),
                    fill_color=T["accent"],
                ),
                ft.Radio(
                    value="specific",
                    label="Mercado específico escolhido por mim",
                    label_style=ft.TextStyle(size=13, color=T["textPrimary"]),
                    fill_color=T["accent"],
                ),
            ],
            spacing=4,
        ),
        value="all" if is_all_markets else "specific",
        on_change=on_mode_change,
    )

    error_text = ft.Text("", size=11, color=T["danger"], visible=False)

    def handle_save(_: Any = None) -> None:
        city = input_city.value.strip()
        if not city:
            error_text.value = "Informe o nome da sua cidade."
            error_text.visible = True
            page.update()
            return

        mode = radio_group.value
        if mode == "specific":
            market = input_market.value.strip()
            if not market:
                error_text.value = "Digite o nome do mercado específico desejado."
                error_text.visible = True
                page.update()
                return
        else:
            market = None

        # Salva no client storage local para próximas sessões
        try:
            set_local_item(page, "shopping_city", city)
            set_local_item(page, "shopping_market", market or "")
        except Exception:
            pass

        close_dlg()
        on_location_saved(city, market)

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
                ft.Text("Salvar", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=T["accent"],
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        ),
        height=38,
        on_click=handle_save,
    )

    content_col = ft.Column(
        [
            input_city,
            ft.Text("Modo de Cotação:", size=12, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
            radio_group,
            input_market,
            error_text,
        ],
        spacing=10,
        tight=True,
    )

    dlg_header = build_modal_header(
        title="Localização & Mercado",
        subtitle="Defina sua cidade e preferência de mercado",
        icon=ft.Icons.LOCATION_ON,
        on_close=close_dlg,
        theme_mode=mode_str,
    )

    dlg.title = dlg_header
    dlg.content = ft.Container(content=content_col, width=360, padding=ft.Padding.only(top=4))
    dlg.actions = [btn_cancel, btn_save]
    dlg.actions_alignment = ft.MainAxisAlignment.END
    dlg.bgcolor = T["surface"]

    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()
