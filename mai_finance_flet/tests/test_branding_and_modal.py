"""
test_branding_and_modal.py — Testes unitários para o Design System, MaiLoading e modais padronizados.
Cobre:
- Componente MaiLoading e utilitários
- Contraste de badges dinâmicos (get_badge_colors)
- Modal de Despesas (fechamento determinístico, sem duplicatas)
- CloneMonthModal (tema Light/Dark, cabeçalho unificado, fluxo de clonagem)
- CategoriesModal (tema Light/Dark, cards adaptados, badges contrastantes)
- BackupModal (tema Light/Dark, cabeçalho unificado, snapshots)
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest
import flet as ft

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from ui.components.mai_loading import MaiLoading
from ui.theme import get_badge_colors, get_tokens
from ui.dashboard_view import DashboardView
from ui.clone_month_modal import CloneMonthModal, open_clone_month_modal
from ui.categories_modal import CategoriesModal, open_categories_modal
from ui.backup_modal import BackupModal, open_backup_modal


class TestBrandingAndLoading:
    def test_mai_loading_instantiation(self):
        loading = MaiLoading(message="Carregando dados...", size=40)
        assert loading is not None
        assert loading.content is not None

    def test_mai_loading_full_screen_overlay(self):
        overlay = MaiLoading.full_screen_overlay(message="Autenticando...", theme_mode="dark")
        assert overlay is not None
        assert overlay.expand is True

    def test_mai_loading_button_spinner(self):
        spinner = MaiLoading.button_spinner(label="Salvando...")
        assert spinner is not None
        assert len(spinner.controls) == 2

    def test_get_badge_colors_dark_and_light(self):
        # Cor amarela de categoria no dark mode
        bg_dark, text_dark, border_dark = get_badge_colors("#FBBF24", is_light=False)
        assert text_dark
        assert bg_dark

        # No tema claro, o texto deve ser escuro para legibilidade garantida
        bg_light, text_light, border_light = get_badge_colors("#FBBF24", is_light=True)
        assert text_light != "#FFFFFF"
        assert border_light is not None

    @patch("ui.dashboard_view.create_expense")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_expense_modal_close_and_save_flow(self, mock_summary, mock_expenses, mock_create):
        mock_expenses.return_value = []
        mock_summary.return_value = {
            "total_despesas": 0.0,
            "total_pago": 0.0,
            "total_pendente": 0.0,
            "qtd_pendente": 0,
            "percent_pago": 100.0,
        }
        mock_create.return_value = {"id": "new-1", "description": "Conta de Água", "amount": 85.0}

        page = MagicMock(spec=ft.Page)
        page.width = 1024
        view = DashboardView(page=page)

        # Abre o diálogo de nova despesa
        view._open_expense_dialog()
        assert page.show_dialog.called or (hasattr(page, "dialog") and page.dialog is not None)

        dlg = page.show_dialog.call_args[0][0]
        assert "Nova Despesa" in dlg.title.value

        # Preenche os campos do modal e clica em Salvar
        col = dlg.content.content
        desc_field = col.controls[0]
        row_amount_due = col.controls[1]
        amount_field = row_amount_due.controls[0]
        due_date_field = row_amount_due.controls[1]

        desc_field.value = "Conta de Água"
        amount_field.value = "85,50"
        due_date_field.value = "2026-09-15"

        btn_save = dlg.actions[1]

        # Simula o clique em Salvar
        btn_save.on_click(None)

        # Valida que create_expense foi chamado com os valores corretos
        assert mock_create.called
        call_args = mock_create.call_args[0][0]
        assert call_args["description"] == "Conta de Água"
        assert call_args["amount"] == 85.50
        assert call_args["due_date"] == "2026-09-15"

        # Valida que o modal foi marcado para fechar (dlg.open = False)
        assert dlg.open is False

        # Valida que uma notificação SnackBar foi exibida
        assert page.snack_bar is not None
        assert page.snack_bar.open is True


class TestStandardizedModals:
    def _create_mock_page(self, theme_mode="dark"):
        page = MagicMock(spec=ft.Page)
        page.width = 1024
        page._mai_storage = {"theme_mode": theme_mode}
        page.session = None
        page.shared_preferences = None
        page.client_storage = None
        return page

    @patch("ui.clone_month_modal.clone_month")
    def test_clone_month_modal_dark_and_light(self, mock_clone):
        mock_clone.return_value = [{"id": "c1"}, {"id": "c2"}]

        # 1. Validação no Tema Claro
        page_light = self._create_mock_page(theme_mode="light")
        modal_light = CloneMonthModal(page=page_light, current_month_ref="2026-09-01")
        assert "Clonar Despesas de um Mês" in modal_light.title.value
        assert modal_light.theme_mode == "light"
        assert modal_light.bgcolor == "#FFFFFF"

        # 2. Validação no Tema Escuro
        page_dark = self._create_mock_page(theme_mode="dark")
        modal_dark = CloneMonthModal(page=page_dark, current_month_ref="2026-09-01")
        assert modal_dark.theme_mode == "dark"
        assert modal_dark.bgcolor == "#121628"

        # 3. Disparo de clonagem com sucesso
        on_cloned_mock = MagicMock()
        modal_dark.on_cloned = on_cloned_mock
        modal_dark.from_dropdown.value = "2026-09"
        modal_dark.to_dropdown.value = "2026-10"

        modal_dark.btn_confirm.on_click(None)
        assert mock_clone.called
        assert on_cloned_mock.called
        assert modal_dark.open is False

    @patch("ui.categories_modal.list_categories")
    def test_categories_modal_dark_and_light(self, mock_list):
        mock_list.return_value = [
            {"id": "cat-1", "name": "Alimentação", "color": "#5EA8F2"},
            {"id": "cat-2", "name": "Lazer", "color": "#FBBF24"},
        ]

        # 1. Validação no Tema Claro
        page_light = self._create_mock_page(theme_mode="light")
        modal_light = CategoriesModal(page=page_light)
        assert "Gerenciar Categorias" in modal_light.title.value
        assert modal_light.theme_mode == "light"
        assert modal_light.card_bg == "#F8FAFC"
        assert len(modal_light.categories_list.controls) == 2

        # 2. Validação no Tema Escuro
        page_dark = self._create_mock_page(theme_mode="dark")
        modal_dark = CategoriesModal(page=page_dark)
        assert modal_dark.theme_mode == "dark"
        assert modal_dark.card_bg == "#151B2E"

    @patch("ui.backup_modal.list_backups")
    @patch("ui.backup_modal.create_manual_backup")
    def test_backup_modal_dark_and_light(self, mock_create_backup, mock_list_backups):
        mock_list_backups.return_value = [
            {
                "id": "b-1",
                "type": "manual",
                "created_at": "2026-09-17T12:00:00",
                "categories_count": 5,
                "expenses_count": 20,
                "total_amount": 3500.0,
            }
        ]

        # 1. Validação no Tema Claro
        page_light = self._create_mock_page(theme_mode="light")
        modal_light = BackupModal(page=page_light)
        assert "Backups do Sistema" in modal_light.title.value
        assert modal_light.theme_mode == "light"
        assert modal_light.card_bg == "#F8FAFC"

        # 2. Validação no Tema Escuro
        page_dark = self._create_mock_page(theme_mode="dark")
        modal_dark = BackupModal(page=page_dark)
        assert modal_dark.theme_mode == "dark"
        assert modal_dark.card_bg == "#151B2E"

        # 3. Criação de backup manual
        modal_dark.btn_create.on_click(None)
        assert mock_create_backup.called
