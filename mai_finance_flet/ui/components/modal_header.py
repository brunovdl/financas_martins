"""
modal_header.py — Cabeçalho unificado para diálogos e modais do MAI Finance.
Garante paridade estética absoluta (mini-logo oficial + título + botão 'X' de fechar).
"""
from __future__ import annotations

from typing import Callable
import flet as ft


def build_modal_header(
    title: str,
    on_close: Callable[[], None],
    theme_tokens: dict[str, str] | None = None,
    **kwargs: Any,
) -> ft.Row:
    """Cria o cabeçalho padronizado do Design System para todos os modais."""
    if theme_tokens is None:
        mode = kwargs.get("theme_mode", "dark")
        try:
            from ui.theme import get_tokens
            tokens = get_tokens(mode)
        except Exception:
            tokens = {"textPrimary": "#EDF0F7", "textMuted": "#8891A8"}
    else:
        tokens = theme_tokens

    header = ft.Row(
        controls=[
            ft.Row(
                controls=[
                    ft.Image(src="logo.png", width=22, height=22, fit=ft.BoxFit.CONTAIN),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=tokens.get("textPrimary", "#EDF0F7")),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=18,
                icon_color=tokens.get("textMuted", "#8891A8"),
                tooltip="Fechar",
                on_click=lambda _: on_close(),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    # Permite compatibilidade com testes que inspecionam dlg.title.value
    header.value = title
    return header

