"""
Testes unitários de navegação e integração do ícone de Lista de Compras no Dashboard (T-021, US-014, AC-030).
"""
from unittest.mock import MagicMock, patch
import flet as ft
import pytest

from ui.nav import create_bottom_nav_bar
from ui.dashboard_view import DashboardView


def test_create_bottom_nav_bar_with_shopping():
    """Valida a criação da barra de navegação incluindo o destino Compras."""
    tab_selected = []
    nav = create_bottom_nav_bar(
        on_change_tab=lambda idx: tab_selected.append(idx),
        selected_index=0,
        include_shopping=True,
    )
    assert len(nav.destinations) == 5
    labels = [d.label for d in nav.destinations]
    assert labels == ["Início", "Categorias", "Compras", "Clonar", "Backups"]
    assert nav.destinations[2].icon == ft.Icons.SHOPPING_BAG_OUTLINED
    assert nav.destinations[2].selected_icon == ft.Icons.SHOPPING_BAG

    # Simula troca de aba para Compras
    nav.on_change(MagicMock(data="2"))
    assert tab_selected == [2]


def test_dashboard_header_shopping_icon_click_opens_shopping():
    """Valida que o clique no ícone de compras do cabeçalho dispara on_open_shopping."""
    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 1024
    opened = []

    with patch("db.shopping.list_shopping_items", return_value=[{"id": "1", "is_bought": False}]):
        view = DashboardView(page=mock_page, on_open_shopping=lambda: opened.append(True))
        assert hasattr(view, "btn_shopping_header_box")
        assert view.btn_shopping_header_box in view.account_row.controls

        # Dispara o on_click do ícone no cabeçalho
        view.btn_shopping_header_box.on_click(None)
        assert len(opened) == 1


def test_dashboard_header_shopping_badge_counter():
    """Valida que o ícone do cabeçalho exibe badge numérico quando há itens pendentes."""
    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 360

    fake_items = [
        {"id": "1", "name": "Arroz", "is_bought": False},
        {"id": "2", "name": "Feijão", "is_bought": False},
        {"id": "3", "name": "Açúcar", "is_bought": True},
    ]

    with patch("db.shopping.list_shopping_items", return_value=fake_items):
        view = DashboardView(page=mock_page)
        view._update_shopping_card_ui()

        assert hasattr(view, "shopping_badge")
        assert view.shopping_badge.visible is True
        assert view.shopping_badge_text.value == "2"
        assert "2 pendentes" in view.btn_shopping_header_box.tooltip


def test_dashboard_header_shopping_badge_hidden_when_empty():
    """Valida que o badge fica oculto e ícone limpo quando não há pendências."""
    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 360

    with patch("db.shopping.list_shopping_items", return_value=[{"id": "1", "is_bought": True}]):
        view = DashboardView(page=mock_page)
        view._update_shopping_card_ui()
        assert view.shopping_badge.visible is False
        assert view.btn_shopping_header_box.tooltip == "Lista de Compras"

    with patch("db.shopping.list_shopping_items", return_value=[]):
        view = DashboardView(page=mock_page)
        view._update_shopping_card_ui()
        assert view.shopping_badge.visible is False


def test_dashboard_main_column_does_not_contain_bulky_card():
    """Garante que o card volumoso foi removido da main_column para otimização de telas pequenas."""
    mock_page = MagicMock(spec=ft.Page)
    mock_page.width = 360

    view = DashboardView(page=mock_page)
    # Card volumoso não deve mais estar ocupando espaço na main_column
    assert view.card_shopping not in view.main_column.controls
