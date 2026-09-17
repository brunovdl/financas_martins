"""
test_nav.py — Testes para navegação principal e alternância de tema (T-012).

Cobre o critério de aceite / história:
- US-009 — Tema visual dark/light e navegação principal
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock
import pytest
import flet as ft

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from ui.nav import get_current_theme, toggle_theme, create_bottom_nav_bar
from ui.theme import THEMES, get_tokens


class TestNavAndTheme:
    def test_themes_structure_and_tokens(self):
        dark = get_tokens("dark")
        light = get_tokens("light")

        assert dark["pageBg"] != light["pageBg"]
        assert dark["accent"] == "#3FD6C4"
        assert light["accent"] == "#0E9488"
        assert "surfaceSolid" in dark
        assert "border" in dark

    def test_get_current_theme_default_dark(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.session = None
        mock_page.shared_preferences = None
        mock_page.client_storage = None
        mock_page._mai_storage = {}

        assert get_current_theme(mock_page) == "dark"

    def test_toggle_theme_switches_modes(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.session = None
        mock_page.shared_preferences = None
        mock_page.client_storage = None
        mock_page._mai_storage = {}

        # 1. Alterna para light
        t1 = toggle_theme(mock_page)
        assert t1 == "light"
        assert get_current_theme(mock_page) == "light"
        assert mock_page.theme_mode == ft.ThemeMode.LIGHT

        # 2. Alterna de volta para dark
        t2 = toggle_theme(mock_page)
        assert t2 == "dark"
        assert get_current_theme(mock_page) == "dark"
        assert mock_page.theme_mode == ft.ThemeMode.DARK

    def test_create_bottom_nav_bar_has_four_destinations(self):
        nav = create_bottom_nav_bar(on_change_tab=lambda idx: None, selected_index=0)
        assert len(nav.destinations) == 4
        labels = [d.label for d in nav.destinations]
        assert "Início" in labels
        assert "Categorias" in labels
        assert "Clonar" in labels
        assert "Backups" in labels
