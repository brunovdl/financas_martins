"""
nav.py — Navegação e gerenciamento de tema visual (Dark / Light) do MAI Finance.

Implementa:
- Alternância dinâmica entre tema escuro e tema claro com persistência em local storage (US-009)
- Barra de navegação responsiva (ft.NavigationBar) para telas menores e atalhos rápidos
- Cores e tokens integrados com o Design System MAI Finance
"""
from __future__ import annotations

from typing import Callable
import flet as ft

from ui.storage_util import get_local_item, set_local_item
from ui.theme import get_tokens


def get_current_theme(page: ft.Page) -> str:
    """Retorna o modo de tema salvo ('dark' ou 'light'), padrão 'dark'."""
    saved = get_local_item(page, "theme_mode")
    return saved if saved in ("dark", "light") else "dark"


def toggle_theme(page: ft.Page) -> str:
    """Alterna entre dark e light e persiste no client storage (US-009)."""
    current = get_current_theme(page)
    new_theme = "light" if current == "dark" else "dark"
    set_local_item(page, "theme_mode", new_theme)

    tokens = get_tokens(new_theme)
    page.theme_mode = ft.ThemeMode.LIGHT if new_theme == "light" else ft.ThemeMode.DARK
    page.bgcolor = tokens["pageBg"]
    page.update()
    return new_theme


def create_bottom_nav_bar(
    on_change_tab: Callable[[int], None],
    selected_index: int = 0,
    include_shopping: bool = False,
) -> ft.NavigationBar:
    """
    Cria a barra de navegação responsiva do MAI Finance.
    Se include_shopping=True, adiciona o destino Compras (AC-030).
    """
    destinations = [
        ft.NavigationBarDestination(
            icon=ft.Icons.HOME_OUTLINED,
            selected_icon=ft.Icons.HOME,
            label="Início",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.LABEL_OUTLINED,
            selected_icon=ft.Icons.LABEL,
            label="Categorias",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.COPY_ALL_OUTLINED,
            selected_icon=ft.Icons.COPY_ALL,
            label="Clonar",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.BACKUP_OUTLINED,
            selected_icon=ft.Icons.BACKUP,
            label="Backups",
        ),
    ]

    if include_shopping:
        destinations.insert(
            2,
            ft.NavigationBarDestination(
                icon=ft.Icons.SHOPPING_BAG_OUTLINED,
                selected_icon=ft.Icons.SHOPPING_BAG,
                label="Compras",
            ),
        )

    return ft.NavigationBar(
        destinations=destinations,
        selected_index=selected_index,
        on_change=lambda e: on_change_tab(int(e.data or 0)),
        bgcolor="#151B2E",
        indicator_color="#3FD6C4",
    )
