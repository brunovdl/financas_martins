"""
test_dashboard_view.py — Testes da view do dashboard e integração de UI (T-005).

Cobre os critérios de aceite:
- @spec:AC-005 — Listagem filtrada por month_ref
- @spec:AC-006 — Cards de resumo usando a view monthly_summary
- @spec:AC-007 — ProgressRing proporcional ao status
- @spec:AC-008 — CRUD completo de despesas
- @spec:AC-009 — Marcar despesa como paga preenche payment_date
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest
import flet as ft

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-para-testes-unitarios")

from ui.dashboard_view import DashboardView
from ui.components.progress_ring import FinancialProgressRing
from ui.theme import (
    format_brl,
    month_label,
    shift_month,
    get_max_days_in_month,
    format_payment_date_to_ui,
    iso_to_br_date,
    br_to_iso_date,
    get_tokens,
)


# ---------------------------------------------------------------------------
# Testes de Formatação e Tema
# ---------------------------------------------------------------------------

class TestThemeHelpers:
    def test_format_brl(self):
        assert format_brl(0) == "R$ 0,00"
        assert format_brl(1234.56) == "R$ 1.234,56"
        assert format_brl(50.5) == "R$ 50,50"
        assert format_brl(None) == "R$ 0,00"
        assert format_brl(1234.56, hide_values=True) == "R$ •••••"
        assert format_brl(0, hide_values=True) == "R$ •••••"
        assert format_brl(None, hide_values=True) == "R$ •••••"

    def test_month_label(self):
        assert month_label("2026-09") == "Setembro 2026"
        assert month_label("2026-01") == "Janeiro 2026"
        assert month_label("2026-12") == "Dezembro 2026"

    def test_shift_month(self):
        assert shift_month("2026-09", 1) == "2026-10"
        assert shift_month("2026-09", -1) == "2026-08"
        assert shift_month("2026-12", 1) == "2027-01"
        assert shift_month("2026-01", -1) == "2025-12"

    def test_get_max_days_in_month(self):
        assert get_max_days_in_month("2026-02") == 28
        assert get_max_days_in_month("2024-02") == 29  # bissexto
        assert get_max_days_in_month("2026-04") == 30
        assert get_max_days_in_month("2026-05") == 31

    def test_format_payment_date_to_ui(self):
        assert format_payment_date_to_ui("2026-09-15") == "15/09/2026"
        assert format_payment_date_to_ui("2026-04-02") == "02/04/2026"
        assert format_payment_date_to_ui(None) == ""

    def test_iso_to_br_date(self):
        assert iso_to_br_date("2026-09-15") == "15/09/2026"
        assert iso_to_br_date("2026-01-05") == "05/01/2026"
        assert iso_to_br_date("15/09/2026") == "15/09/2026"
        assert iso_to_br_date("") == ""
        assert iso_to_br_date(None) == ""

    def test_br_to_iso_date(self):
        assert br_to_iso_date("15/09/2026") == "2026-09-15"
        assert br_to_iso_date("05-01-2026") == "2026-01-05"
        assert br_to_iso_date("2026-09-15") == "2026-09-15"
        assert br_to_iso_date("") == ""
        assert br_to_iso_date(None) == ""


# ---------------------------------------------------------------------------
# AC-005: Listagem filtrada por month_ref
# @spec:AC-005
# ---------------------------------------------------------------------------

class TestDashboardViewListing:
    """@spec:AC-005 — Listagem de despesas e navegação entre meses."""

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_month_navigation_shifts_ref_and_reloads(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {
            "total_despesas": 0.0,
            "total_pago": 0.0,
            "total_pendente": 0.0,
            "qtd_pendente": 0,
            "percent_pago": 100.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        initial_month = view.current_month_ref

        # Avança 1 mês
        view._change_month(1)
        expected_next = shift_month(initial_month, 1)
        assert view.current_month_ref == expected_next
        assert view.month_display.value == month_label(expected_next)
        mock_expenses.assert_called_with(expected_next)

        # Volta 1 mês
        view._change_month(-1)
        assert view.current_month_ref == initial_month


# ---------------------------------------------------------------------------
# AC-006 & AC-007: Resumo mensal e anel de progresso
# @spec:AC-006, @spec:AC-007
# ---------------------------------------------------------------------------

class TestDashboardSummaryCards:
    """@spec:AC-006, @spec:AC-007 — Cards de resumo e anel de progresso."""

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_summary_cards_display_accurate_values(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {
            "total_despesas": 4000.0,
            "total_pago": 3000.0,
            "total_pendente": 1000.0,
            "qtd_pendente": 2,
            "percent_pago": 75.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        assert view.card_total_val.value == "R$ 4.000,00"
        assert view.card_pago_val.value == "R$ 3.000,00"
        assert view.card_pendente_val.value == "R$ 1.000,00"
        assert "2 pendências" in view.card_pendente_badge.value
        assert view.progress_ring.ring.value == 0.75
        assert view.progress_ring.label.value == "75%"


# ---------------------------------------------------------------------------
# AC-008 & AC-009: Ações de status, busca e filtros
# @spec:AC-008, @spec:AC-009
# ---------------------------------------------------------------------------

class TestDashboardFiltersAndActions:
    """@spec:AC-008, @spec:AC-009 — Filtros e alternância de status."""

    @patch("ui.dashboard_view.toggle_expense_status")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_toggle_status_triggers_service(self, mock_summary, mock_expenses, mock_toggle):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Luz", "amount": 150.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {
            "total_despesas": 150.0,
            "total_pago": 0.0,
            "total_pendente": 150.0,
            "qtd_pendente": 1,
            "percent_pago": 0.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        view._toggle_status("exp-1", "pendente")
        mock_toggle.assert_called_once_with("exp-1", "pendente")

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_search_and_status_filtering(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1200.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 120.0, "status": "pendente", "due_date": "2026-09-10"},
            {"id": "exp-3", "description": "Supermercado", "amount": 500.0, "status": "pendente", "due_date": "2026-09-15"},
        ]
        mock_summary.return_value = {"total_despesas": 1820.0, "total_pago": 1200.0, "total_pendente": 620.0, "qtd_pendente": 2, "percent_pago": 65.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Filtro de status: apenas pendente
        view.status_filter = "pendente"
        view._render_expenses_list()
        assert len(view.expenses_list_col.controls) == 2

        # Filtro de status: apenas pago
        view.status_filter = "pago"
        view._render_expenses_list()
        assert len(view.expenses_list_col.controls) == 1

        # Filtro de busca textual
        view.status_filter = "todos"
        view.search_query = "Internet"
        view._render_expenses_list()
        assert len(view.expenses_list_col.controls) == 1

    @patch("ui.dashboard_view.update_expense")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_inline_editing_commit(self, mock_summary, mock_expenses, mock_update):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Luz", "amount": 150.0, "status": "pendente", "due_date": "2026-09-10", "observation": "Pix"}
        ]
        mock_summary.return_value = {"total_despesas": 150.0, "total_pago": 0.0, "total_pendente": 150.0, "qtd_pendente": 1, "percent_pago": 0.0}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Edição inline de descrição
        view._commit_inline_edit("exp-1", "description", "Energia Solar")
        mock_update.assert_called_with("exp-1", {"description": "Energia Solar"})

        # Edição inline de valor
        view._commit_inline_edit("exp-1", "amount", "250,50")
        mock_update.assert_called_with("exp-1", {"amount": 250.50})

        # Edição inline de observação
        view._commit_inline_edit("exp-1", "observation", "Chave 12345")
        mock_update.assert_called_with("exp-1", {"observation": "Chave 12345"})


class TestDashboardQAFixes:
    """Validação das correções do relatório de QA."""

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_responsive_mobile_cards_vs_desktop_table(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Luz", "amount": 150.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {"total_despesas": 150.0, "total_pago": 0.0, "total_pendente": 150.0, "qtd_pendente": 1, "percent_pago": 0.0}

        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 400  # Mobile
        view = DashboardView(page=mock_page)
        view.is_mobile = True
        view.load_data(silent=True)

        assert view.table_header.visible is False
        assert len(view.expenses_list_col.controls) == 1

        # Desktop
        view.is_mobile = False
        view.table_header.visible = True
        view._render_expenses_list()
        assert view.table_header.visible is True
        assert len(view.expenses_list_col.controls) == 1

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_apply_theme_updates_all_structural_containers(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)

        # Alterna para light
        view.theme_mode = "light"
        view._apply_theme()
        light_tokens = view.T
        assert view.bgcolor == light_tokens["pageBg"]
        assert view.card_total.bgcolor == light_tokens["surfaceSolid"]
        assert view.card_pago.bgcolor == light_tokens["surfaceSolid"]
        assert view.card_pendente.bgcolor == light_tokens["surfaceSolid"]
        assert view.search_field.bgcolor == light_tokens["surfaceSolid"]
        assert view.progress_ring.label.color == light_tokens["textPrimary"]
        assert view.progress_ring.ring.bgcolor == light_tokens["ringTrack"]

    def test_dashboard_initializes_with_json_string_user_data(self):
        mock_page = MagicMock(spec=ft.Page)
        with patch("ui.dashboard_view.get_local_item", return_value='{"name": "Maria", "email": "maria@example.com"}'):
            view = DashboardView(page=mock_page)
            assert view.user_name == "Maria"
            assert view.user_email == "maria@example.com"

    @patch("ui.dashboard_view.get_previous_month_pending")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_prev_month_alert_updates_badge_and_modal(self, mock_summary, mock_expenses, mock_pending):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}
        mock_pending.return_value = {
            "prev_month_ref": "2026-08",
            "items": [{"id": "exp-prev", "description": "Condomínio", "amount": 300.0}],
            "count": 1,
            "total_amount": 300.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        mock_page.show_dialog = MagicMock()
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        assert view.alert_badge.visible is True
        assert view.alert_badge_text.value == "1"

        # Abre o modal de alerta
        view._open_prev_month_alert_modal()
        mock_page.show_dialog.assert_called_once()
        dlg = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dlg, ft.AlertDialog)
        assert "Pendências de Agosto 2026" in dlg.title.value

        # Encontra o botão de navegação da despesa no modal
        content_container = dlg.content
        items_list = content_container.content.controls[1]
        assert len(items_list.controls) == 1
        item_row = items_list.controls[0]
        # Dispara navegação direta para a despesa
        item_row.on_click(None)

        # Valida que navegou para o mês anterior com a despesa em foco
        assert view.current_month_ref == "2026-08"
        assert view.status_filter == "pendente"
        assert view.search_query == "Condomínio"

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_open_expense_dialog_uses_show_dialog(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}

        mock_page = MagicMock(spec=ft.Page)
        mock_page.show_dialog = MagicMock()
        view = DashboardView(page=mock_page)

        view._open_expense_dialog()
        mock_page.show_dialog.assert_called_once()

    def test_summary_bar_layout_desktop_and_mobile(self):
        """Verifica que o summary_bar usa ft.Row no desktop e layout em 2 níveis no mobile."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 1024
        view = DashboardView(page=mock_page)

        # Em desktop (>=768px): summary_bar deve ser ft.Row com cards expandidos e sem wrap
        assert isinstance(view.summary_bar, ft.Row)
        assert getattr(view.summary_bar, "wrap", False) is False
        assert view.card_total.expand is True
        assert view.card_pago.expand is True
        assert view.card_pendente.expand is True

        # Simula redimensionamento para mobile (<768px)
        mock_page.width = 360
        view._handle_page_resized(None)
        assert view.is_mobile is True
        assert isinstance(view.summary_bar, ft.Column)
        # Nível 1: card_total (largura cheia, expand=False na coluna)
        assert view.card_total.expand is False
        # Nível 2: ft.Row com card_pago e card_pendente lado a lado (expand=True na row)
        assert len(view.summary_bar.controls) == 2
        tier2 = view.summary_bar.controls[1]
        assert isinstance(tier2, ft.Row)
        assert view.card_pago.expand is True
        assert view.card_pendente.expand is True

    def test_mobile_floating_action_button_and_popup_menu(self):
        """Verifica que o mobile ativa o FAB e recolhe ações secundárias no menu popup MORE_VERT."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 360
        view = DashboardView(page=mock_page)

        # No mobile: FAB ativo, Nova Despesa oculta da barra, menu de 3 pontinhos visível
        assert view.is_mobile is True
        assert mock_page.floating_action_button is not None
        assert mock_page.floating_action_button.icon == ft.Icons.ADD
        assert view.btn_nova_despesa.visible is False
        assert view.btn_categorias.visible is False
        assert view.btn_clonar.visible is False
        assert view.btn_backups.visible is False
        assert view.btn_more_options.visible is True
        assert len(view.btn_more_options.items) == 6

        # Transição para desktop (1024px)
        mock_page.width = 1024
        view._handle_page_resized(None)
        assert view.is_mobile is False
        assert mock_page.floating_action_button is None
        assert view.btn_nova_despesa.visible is True
        assert view.btn_categorias.visible is True
        assert view.btn_clonar.visible is True
        assert view.btn_backups.visible is True
        assert view.btn_more_options.visible is False

    def test_header_layout_mobile_two_rows_vs_desktop_single_row(self):
        """Verifica que o cabeçalho fica em 2 linhas no mobile e em linha única no desktop."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 1200
        view = DashboardView(page=mock_page)

        # Desktop: linha única com 3 seções (Logo/Usuário, Seletor de Mês, Conta)
        assert view.is_mobile is False
        assert view.header_container.content == view.header_row
        assert isinstance(view.header_row, ft.Row)
        assert len(view.header_row.controls) == 3

        # Mobile: 2 linhas verticais (Linha 1: Logo + Conta, Linha 2: Seletor Mês)
        mock_page.width = 360
        view._handle_page_resized(None)
        assert view.is_mobile is True
        assert view.header_container.content == view.header_mobile_col
        assert isinstance(view.header_mobile_col, ft.Column)
        assert len(view.header_mobile_col.controls) == 2

    def test_header_row_single_line_layout(self):
        """Verifica que o cabeçalho desktop fica em linha única sem quebra (wrap=False)."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 1200
        view = DashboardView(page=mock_page)

        assert isinstance(view.header_row, ft.Row)
        assert getattr(view.header_row, "wrap", False) is False
        assert view.header_row.alignment == ft.MainAxisAlignment.SPACE_BETWEEN
        # 3 controles principais: Logo/Usuário, Seletor de Mês e Ações da Conta
        assert len(view.header_row.controls) == 3

    def test_action_filter_bar_single_line_icon_buttons(self):
        """Verifica que a barra de ações fica em linha única e usa botões de ícone com tooltip."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 1200
        view = DashboardView(page=mock_page)

        assert isinstance(view.action_filter_bar, ft.Row)
        assert getattr(view.action_filter_bar, "wrap", False) is False

        # Nova Despesa continua com botão em destaque no desktop
        assert isinstance(view.btn_nova_despesa, ft.Button)

        # Categorias, Clonar Mês e Backups são IconButtons compactos com tooltip
        assert isinstance(view.btn_categorias, ft.IconButton)
        assert view.btn_categorias.tooltip == "Categorias"

        assert isinstance(view.btn_clonar, ft.IconButton)
        assert view.btn_clonar.tooltip == "Clonar Mês"

        assert isinstance(view.btn_backups, ft.IconButton)
        assert view.btn_backups.tooltip == "Backups"

    def test_status_filter_button_strict_height_and_functionality(self):
        """Verifica que o seletor de status tem altura estrita de 38px e sincroniza valores corretamente."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 1200
        view = DashboardView(page=mock_page)

        # Verifica tipo e propriedades de altura e padding
        selector = view.filter_dropdown
        assert isinstance(selector, ft.PopupMenuButton)
        assert selector.padding == 0
        assert view.filter_dropdown_container.height == 38
        assert view.filter_dropdown_container.border_radius == 8

        # Estado inicial
        assert selector.value == "todos"
        assert view.filter_status_text.value == "Todos os status"

        # Atualização programática (ex: navegação para pendências)
        view._on_status_filter_selected("pendente")
        assert selector.value == "pendente"
        assert view.filter_status_text.value == "Pendentes"

        view._on_status_filter_selected("pago")
        assert selector.value == "pago"
        assert view.filter_status_text.value == "Pagos"

        # Compatibilidade com tema
        view._apply_theme()
        assert view.filter_dropdown_container.bgcolor == view.T["surfaceSolid"]


class TestDashboardResponsiveBreakpoints:
    """Testes formais dos 3 breakpoints de viewport:
    1. Mobile (< 768px)
    2. Compacto / Tablet / Janela Média (768px <= width < 1024px)
    3. Desktop Amplo (>= 1024px)
    """

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_mobile_viewport_behavior(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Energia Elétrica", "amount": 250.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {"total_despesas": 250.0, "total_pago": 0.0, "total_pendente": 250.0, "qtd_pendente": 1, "percent_pago": 0.0}

        page = MagicMock(spec=ft.Page)
        page.width = 360
        view = DashboardView(page=page)
        view.load_data(silent=True)

        assert view.is_mobile is True
        assert view.is_compact is True
        # Cabeçalho em 2 linhas
        assert view.header_container.content == view.header_mobile_col
        # Resumo em 2 níveis
        assert isinstance(view.summary_bar, ft.Column)
        # Botão Nova Despesa migra para FAB
        assert view.btn_nova_despesa.visible is False
        assert page.floating_action_button is not None
        # Menu 3 pontinhos visível, botões individuais ocultos
        assert view.btn_more_options.visible is True
        assert view.btn_categorias.visible is False
        # Tabela oculta, usa Cards
        assert view.table_header.visible is False
        assert len(view.expenses_list_col.controls) == 1
        # Card tem formato de coluna (não de linha de tabela)
        assert isinstance(view.expenses_list_col.controls[0].content, ft.Column)

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_compact_viewport_behavior(self, mock_summary, mock_expenses):
        """Cenário exato do print do usuário (janela em ~850px):
        Não deve quebrar o cabeçalho nem cortar botões."""
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Energia Elétrica", "amount": 250.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {"total_despesas": 250.0, "total_pago": 0.0, "total_pendente": 250.0, "qtd_pendente": 1, "percent_pago": 0.0}

        page = MagicMock(spec=ft.Page)
        page.width = 850
        view = DashboardView(page=page)
        view.load_data(silent=True)

        assert view.is_mobile is False
        assert view.is_compact is True
        # Cabeçalho em linha única
        assert view.header_container.content == view.header_row
        # Resumo em 3 cards horizontais
        assert isinstance(view.summary_bar, ft.Row)
        # Botão Nova Despesa visível na barra (não precisa de FAB)
        assert view.btn_nova_despesa.visible is True
        assert page.floating_action_button is None
        # Ações secundárias agrupadas no menu 3 pontinhos para não estourar a barra
        assert view.btn_more_options.visible is True
        assert view.btn_categorias.visible is False
        assert view.btn_clonar.visible is False
        assert view.btn_backups.visible is False
        # Busca responsiva e seletor de status compacto
        assert view.search_field.expand is True
        assert view.filter_dropdown_container.width == 120
        assert view.filter_status_text.value == "Todos"
        # Tabela oculta para evitar quebra vertical de texto; exibe Cards de despesas
        assert view.table_header.visible is False
        assert len(view.expenses_list_col.controls) == 1
        assert isinstance(view.expenses_list_col.controls[0].content, ft.Column)

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_desktop_wide_viewport_behavior(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Energia Elétrica", "amount": 250.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {"total_despesas": 250.0, "total_pago": 0.0, "total_pendente": 250.0, "qtd_pendente": 1, "percent_pago": 0.0}

        page = MagicMock(spec=ft.Page)
        page.width = 1280
        view = DashboardView(page=page)
        view.load_data(silent=True)

        assert view.is_mobile is False
        assert view.is_compact is False
        # Cabeçalho e resumo amplos
        assert view.header_container.content == view.header_row
        assert isinstance(view.summary_bar, ft.Row)
        # Todos os botões visíveis na barra
        assert view.btn_nova_despesa.visible is True
        assert view.btn_categorias.visible is True
        assert view.btn_clonar.visible is True
        assert view.btn_backups.visible is True
        assert view.btn_more_options.visible is False
        # Busca com largura fixa e seletor com rótulo completo
        assert view.search_field.width == 220
        assert view.search_field.expand is False
        assert view.filter_dropdown_container.width == 165
        assert view.filter_status_text.value == "Todos os status"
        # Tabela visível com cabeçalho de 8 colunas e linhas em ft.Row
        assert view.table_header.visible is True
        assert len(view.expenses_list_col.controls) == 1
        assert isinstance(view.expenses_list_col.controls[0].content, ft.Row)

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_dynamic_on_resize_event_adapts_to_mobile(self, mock_summary, mock_expenses):
        """Valida que disparar on_resize com evento de largura < 768px adapta a view imediatamente."""
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Luz", "amount": 150.0, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {"total_despesas": 150.0, "total_pago": 0.0, "total_pendente": 150.0, "qtd_pendente": 1, "percent_pago": 0.0}

        page = MagicMock(spec=ft.Page)
        page.width = 1200
        view = DashboardView(page=page)
        view.load_data(silent=True)

        assert view.is_mobile is False
        assert view.table_header.visible is True

        # Simula redimensionamento para janela estreita (ex: 500px como no screenshot do usuário)
        resize_event = MagicMock()
        resize_event.width = 500.0
        resize_event.height = 800.0
        view._handle_page_resized(resize_event)

        assert view.is_mobile is True
        assert view.is_compact is True
        assert view.header_container.content == view.header_mobile_col
        assert view.table_header.visible is False
        assert view.btn_more_options.visible is True
        assert len(view.expenses_list_col.controls) == 1
        assert isinstance(view.expenses_list_col.controls[0].content, ft.Column)

    @patch("ui.dashboard_view.create_expense")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_duplicate_expense_flow(self, mock_summary, mock_expenses, mock_create):
        """Valida que duplicar despesa abre modal e cria uma nova despesa via create_expense."""
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Academia", "amount": 120.0, "status": "pago", "due_date": "2026-09-05"}
        ]
        mock_summary.return_value = {"total_despesas": 120.0, "total_pago": 120.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}

        page = MagicMock(spec=ft.Page)
        page.width = 360
        view = DashboardView(page=page)
        view.load_data(silent=True)

        # Dispara abertura de duplicação
        view._open_expense_dialog(mock_expenses.return_value[0], is_duplicate=True)
        assert page.show_dialog.called
        dlg = page.show_dialog.call_args[0][0]
        assert "Duplicar Despesa" in dlg.title.value


class TestFinancialProgressRingUnit:
    """Valida o componente FinancialProgressRing e sua resposta aos temas claro e escuro."""

    def test_progress_ring_defaults(self):
        ring = FinancialProgressRing(pct=35.0)
        assert ring.ring.value == 0.35
        assert ring.label.value == "35%"
        assert ring.label.color == "#F1F5F9"
        assert ring.ring.bgcolor == "#1E293B"

    def test_progress_ring_custom_text_color(self):
        ring = FinancialProgressRing(pct=40.0, text_color="#0F172A")
        assert ring.label.color == "#0F172A"

    def test_progress_ring_set_pct(self):
        ring = FinancialProgressRing(pct=0.0)
        ring.set_pct(88.4)
        assert ring.ring.value == 0.884
        assert ring.label.value == "88%"

    def test_progress_ring_apply_theme_dict(self):
        ring = FinancialProgressRing(pct=50.0)
        light_tokens = get_tokens("light")
        ring.apply_theme(light_tokens)
        assert ring.label.color == light_tokens["textPrimary"]  # Alto contraste contra branco
        assert ring.ring.bgcolor == light_tokens["ringTrack"]
        assert ring.ring.color == light_tokens["ring1"]

        dark_tokens = get_tokens("dark")
        ring.apply_theme(dark_tokens)
        assert ring.label.color == dark_tokens["textPrimary"]
        assert ring.ring.bgcolor == dark_tokens["ringTrack"]
        assert ring.ring.color == dark_tokens["ring1"]

    def test_progress_ring_apply_theme_kwargs(self):
        ring = FinancialProgressRing(pct=50.0)
        ring.apply_theme(text_color="#123456", track_color="#ABCDEF", ring_color="#654321")
        assert ring.label.color == "#123456"
        assert ring.ring.bgcolor == "#ABCDEF"
        assert ring.ring.color == "#654321"


class TestMobileCardObservationAndPendingModal:
    """Valida o indicativo/sanfona de observações no mobile e o layout compacto do modal de pendências."""

    def test_mobile_card_observation_accordion(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        # Despesa com observação
        exp_with_obs = {
            "id": "exp-obs-1",
            "description": "Seguro Carro",
            "amount": 250.0,
            "status": "pendente",
            "due_date": "2026-09-15",
            "observation": "Parcela 3 de 10",
        }
        card = view._build_expense_mobile_card(exp_with_obs)
        col = card.content
        assert isinstance(col, ft.Column)
        # Top row, Desc row, Obs box, Bottom row
        assert len(col.controls) == 4

        desc_row = col.controls[1]
        assert isinstance(desc_row, ft.Row)
        obs_badge = desc_row.controls[1]
        assert isinstance(obs_badge, ft.Container)
        assert obs_badge.content.controls[1].value == "Obs"

        obs_box = col.controls[2]
        assert isinstance(obs_box, ft.Container)
        assert obs_box.visible is False

        # Dispara clique no badge de observação para expandir sanfona
        obs_badge.on_click(None)
        assert obs_box.visible is True

        # Dispara clique novamente para recolher
        obs_badge.on_click(None)
        assert obs_box.visible is False

        # Dispara clique no container de descrição da despesa para expandir
        desc_container = desc_row.controls[0]
        desc_container.on_click(None)
        assert obs_box.visible is True

        # Dispara clique na própria caixa de observação para recolher
        obs_box.on_click(None)
        assert obs_box.visible is False

    def test_mobile_card_without_observation(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        exp_no_obs = {
            "id": "exp-no-obs",
            "description": "Água",
            "amount": 80.0,
            "status": "pago",
            "due_date": "2026-09-08",
            "observation": "",
        }
        card = view._build_expense_mobile_card(exp_no_obs)
        col = card.content
        assert isinstance(col, ft.Column)
        # Apenas Top row, Desc container, Bottom row (sem Obs box)
        assert len(col.controls) == 3

    @patch("ui.dashboard_view.get_previous_month_pending")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_pending_modal_two_line_compact_layout(self, mock_summary, mock_expenses, mock_pending):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}
        mock_pending.return_value = {
            "prev_month_ref": "2026-08",
            "items": [
                {
                    "id": "exp-p1",
                    "description": "Financiamento Apto Araraquara",
                    "amount": 605.05,
                    "due_date": "2026-08-20",
                    "category": {"name": "Moradia", "color": "#3B82F6"},
                }
            ],
            "count": 1,
            "total_amount": 605.05,
        }

        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)
        view.load_data(silent=True)
        view._open_prev_month_alert_modal()

        dlg = page.show_dialog.call_args[0][0]
        items_list = dlg.content.content.controls[1]
        row_item = items_list.controls[0]
        assert isinstance(row_item, ft.Container)

        # O conteúdo interno é uma Column de 2 linhas compactas
        card_col = row_item.content
        assert isinstance(card_col, ft.Column)
        assert len(card_col.controls) == 2

        top_row = card_col.controls[0]
        assert "Moradia" in top_row.controls[0].controls[0].content.value
        assert "Dia 20" in top_row.controls[0].controls[1].content.value
        assert "R$ 605,05" in top_row.controls[1].value

        bottom_row = card_col.controls[1]
        assert "Financiamento Apto Araraquara" in bottom_row.controls[0].value
        assert "Ir" in bottom_row.controls[1].controls[0].value

    def test_clear_filters_and_active_banner_flow(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        # Simula filtros ativos
        view.search_query = "Financiamento"
        view.search_field.value = "Financiamento"
        view.status_filter = "pendente"
        view._update_active_filters_banner()

        assert view.active_filters_banner.visible is True
        assert "Pendentes" in view.active_filter_text.value
        assert "Financiamento" in view.active_filter_text.value
        assert view.btn_clear_search.visible is True

        # Dispara limpeza completa dos filtros
        view._clear_all_filters()

        assert view.search_query == ""
        assert view.search_field.value == ""
        assert view.status_filter == "todos"
        assert view.active_filters_banner.visible is False
        assert view.btn_clear_search.visible is False

    def test_clear_search_button_flow(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        view.search_query = "Luz"
        view.search_field.value = "Luz"
        view._update_active_filters_banner()
        assert view.btn_clear_search.visible is True

        # Limpa apenas a busca
        view._clear_search()
        assert view.search_query == ""
        assert view.search_field.value == ""
        assert view.btn_clear_search.visible is False

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_reset_to_current_month_clears_all_filters(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}

        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        view.current_month_ref = "2026-07"
        view.search_query = "Aluguel"
        view.search_field.value = "Aluguel"
        view.status_filter = "pendente"

        view._reset_to_current_month()

        assert view.search_query == ""
        assert view.search_field.value == ""
        assert view.status_filter == "todos"
        assert view.active_filters_banner.visible is False

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_change_month_clears_search_query(self, mock_summary, mock_expenses):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}

        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        view.search_query = "Mercado"
        view.search_field.value = "Mercado"

        view._change_month(1)

        assert view.search_query == ""
        assert view.search_field.value == ""
        assert view.btn_clear_search.visible is False

    def test_will_unmount_stops_polling_and_fab(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)
        view._polling_active = True
        page.floating_action_button = MagicMock()

        view.will_unmount()

        assert view._polling_active is False
        assert page.floating_action_button is None

    def test_handle_page_resized_optimizes_rendering(self):
        page = MagicMock(spec=ft.Page)
        view = DashboardView(page=page)

        with patch.object(view, "_render_expenses_list") as mock_render:
            # 1. Primeiro resize (montagem inicial): dispara render
            view._handle_page_resized(MagicMock(width=360))
            assert mock_render.call_count == 1

            # 2. Resize dentro do mesmo breakpoint (ex: 365px, ainda mobile): NÃO re-renderiza a lista toda
            view._handle_page_resized(MagicMock(width=365))
            assert mock_render.call_count == 1

            # 3. Transição de breakpoint (ex: 800px, tablet/desktop): dispara render
            view._handle_page_resized(MagicMock(width=800))
            assert mock_render.call_count == 2


class TestMultiSelectionAndStatusStability:
    """Testes para seleção múltipla com barra flutuante e estabilidade do toggle de status."""

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_multi_selection_and_totals_calculation(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1000.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 100.0, "status": "pendente", "due_date": "2026-09-10"},
            {"id": "exp-3", "description": "Energia", "amount": 200.0, "status": "pendente", "due_date": "2026-09-15"},
        ]
        mock_summary.return_value = {"total_despesas": 1300.0, "total_pago": 1000.0, "total_pendente": 300.0, "qtd_pendente": 2, "percent_pago": 76.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        assert view.floating_selection_bar.visible is False

        # Seleciona exp-1 e exp-2
        view._toggle_expense_selection("exp-1", True)
        view._toggle_expense_selection("exp-2", True)

        assert view.selected_expense_ids == {"exp-1", "exp-2"}
        assert view.floating_selection_bar.visible is True

        totals = view._calculate_selected_totals()
        assert totals["count_total"] == 2
        assert totals["total"] == 1100.0
        assert totals["count_pago"] == 1
        assert totals["total_pago"] == 1000.0
        assert totals["count_pendente"] == 1
        assert totals["total_pendente"] == 100.0

        # Desmarca exp-1
        view._toggle_expense_selection("exp-1", False)
        assert view.selected_expense_ids == {"exp-2"}
        totals = view._calculate_selected_totals()
        assert totals["count_total"] == 1
        assert totals["total"] == 100.0

        # Desmarca todos
        view._clear_selection()
        assert len(view.selected_expense_ids) == 0
        assert view.floating_selection_bar.visible is False

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_toggle_select_all_respects_filtered_items(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1000.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 100.0, "status": "pendente", "due_date": "2026-09-10"},
            {"id": "exp-3", "description": "Energia", "amount": 200.0, "status": "pendente", "due_date": "2026-09-15"},
        ]
        mock_summary.return_value = {"total_despesas": 1300.0, "total_pago": 1000.0, "total_pendente": 300.0, "qtd_pendente": 2, "percent_pago": 76.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Filtra apenas pendentes
        view._on_status_filter_selected("pendente")

        # Seleciona todos os visíveis
        view._toggle_select_all(True)
        assert view.selected_expense_ids == {"exp-2", "exp-3"}
        assert "exp-1" not in view.selected_expense_ids

        # Desmarca todos
        view._toggle_select_all(False)
        assert len(view.selected_expense_ids) == 0

    @patch("ui.dashboard_view.delete_expenses_batch")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_batch_delete_selected(self, mock_summary, mock_expenses, mock_batch_delete):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1000.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 100.0, "status": "pendente", "due_date": "2026-09-10"},
        ]
        mock_summary.return_value = {"total_despesas": 1100.0, "total_pago": 1000.0, "total_pendente": 100.0, "qtd_pendente": 1, "percent_pago": 90.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        view._toggle_expense_selection("exp-1", True)
        view._toggle_expense_selection("exp-2", True)

        mock_dlg = MagicMock(spec=ft.AlertDialog)
        view._execute_delete_selected(mock_dlg)

        mock_batch_delete.assert_called_once()
        called_ids = mock_batch_delete.call_args[0][0]
        assert set(called_ids) == {"exp-1", "exp-2"}
        assert len(view.expenses) == 0
        assert len(view.selected_expense_ids) == 0
        assert view.floating_selection_bar.visible is False

    @patch("ui.dashboard_view.toggle_expense_status")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_toggle_status_in_place_preserves_position(self, mock_summary, mock_expenses, mock_toggle):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1000.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 100.0, "status": "pendente", "due_date": "2026-09-10"},
            {"id": "exp-3", "description": "Energia", "amount": 200.0, "status": "pendente", "due_date": "2026-09-15"},
        ]
        mock_summary.return_value = {"total_despesas": 1300.0, "total_pago": 1000.0, "total_pendente": 300.0, "qtd_pendente": 2, "percent_pago": 76.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Alterna status de exp-2 (posição index 1)
        view._toggle_status("exp-2", "pendente")

        # Verifica que exp-2 continua exatamente no index 1
        assert view.expenses[0]["id"] == "exp-1"
        assert view.expenses[1]["id"] == "exp-2"
        assert view.expenses[2]["id"] == "exp-3"

        # Verifica que o status foi atualizado in-place
        assert view.expenses[1]["status"] == "pago"
        assert view.expenses[1]["payment_date"] is not None

        # Verifica que os resumos foram recalculados in-place
        assert view.summary["total_pago"] == 1100.0
        assert view.summary["total_pendente"] == 200.0
        assert view.summary["qtd_pendente"] == 1

        mock_toggle.assert_called_once_with("exp-2", "pendente")

    @patch("ui.dashboard_view.toggle_expense_status")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_toggle_status_under_active_filter_preserves_visibility_and_position(self, mock_summary, mock_expenses, mock_toggle):
        """Garante que ao mudar o status com filtro ativo, a célula permanece visível no mesmo lugar até o filtro ser refeito."""
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Aluguel", "amount": 1000.0, "status": "pago", "due_date": "2026-09-05"},
            {"id": "exp-2", "description": "Internet", "amount": 100.0, "status": "pendente", "due_date": "2026-09-10"},
            {"id": "exp-3", "description": "Energia", "amount": 200.0, "status": "pendente", "due_date": "2026-09-15"},
        ]
        mock_summary.return_value = {"total_despesas": 1300.0, "total_pago": 1000.0, "total_pendente": 300.0, "qtd_pendente": 2, "percent_pago": 76.9}

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # 1. Aplica filtro de pendentes (deve exibir exp-2 e exp-3)
        view._on_status_filter_selected("pendente")
        assert len(view.expenses_list_col.controls) == 2

        # 2. Alterna status de exp-2 para pago
        view._toggle_status("exp-2", "pendente")

        # 3. exp-2 DEVE permanecer visível na lista (2 itens continuam renderizados)
        assert len(view.expenses_list_col.controls) == 2
        assert view.expenses[1]["status"] == "pago"

        # 4. Ao reaplicar explicitamente o filtro de pendentes, a lista se atualiza para 1 item
        view._on_status_filter_selected("pendente")
        assert len(view.expenses_list_col.controls) == 1

        # 5. Ao selecionar filtro de pagos, exibe exp-1 e exp-2 (2 itens)
        view._on_status_filter_selected("pago")
        assert len(view.expenses_list_col.controls) == 2


# ---------------------------------------------------------------------------
# Testes do Modo de Privacidade (Ocultar Valores em Reais)
# ---------------------------------------------------------------------------

class TestDashboardPrivacyAndHideValues:
    """Valida o modo de privacidade para ocultar valores monetários (R$ •••••)."""

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_initial_state_defaults_to_visible(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Conta de Luz", "amount": 250.50, "status": "pendente", "due_date": "2026-09-10"}
        ]
        mock_summary.return_value = {
            "total_despesas": 250.50,
            "total_pago": 0.0,
            "total_pendente": 250.50,
            "qtd_pendente": 1,
            "percent_pago": 0.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        assert view.hide_values is False
        assert view.btn_toggle_hide_values.icon == ft.Icons.VISIBILITY_OUTLINED
        assert view.btn_toggle_hide_values.tooltip == "Ocultar valores"
        assert view.text_toggle_hide_values.value == "Ocultar Valores"
        assert view.card_total_val.value == "R$ 250,50"
        assert view.card_pago_val.value == "R$ 0,00"
        assert view.card_pendente_val.value == "R$ 250,50"

    @patch("ui.dashboard_view.set_local_item")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_toggle_hide_values_updates_cards_and_menu(self, mock_summary, mock_expenses, mock_set_item):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Internet", "amount": 120.0, "status": "pago", "due_date": "2026-09-05"}
        ]
        mock_summary.return_value = {
            "total_despesas": 120.0,
            "total_pago": 120.0,
            "total_pendente": 0.0,
            "qtd_pendente": 0,
            "percent_pago": 100.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # 1. Ativa ocultação de valores
        view._toggle_hide_values()
        assert view.hide_values is True
        assert view.btn_toggle_hide_values.icon == ft.Icons.VISIBILITY_OFF_OUTLINED
        assert view.btn_toggle_hide_values.tooltip == "Mostrar valores"
        assert view.text_toggle_hide_values.value == "Mostrar Valores"
        assert view.card_total_val.value == "R$ •••••"
        assert view.card_pago_val.value == "R$ •••••"
        assert view.card_pendente_val.value == "R$ •••••"
        mock_set_item.assert_called_with(mock_page, "mai_finance_hide_values", True)

        # 2. Desativa ocultação de valores (volta a mostrar)
        view._toggle_hide_values()
        assert view.hide_values is False
        assert view.btn_toggle_hide_values.icon == ft.Icons.VISIBILITY_OUTLINED
        assert view.btn_toggle_hide_values.tooltip == "Ocultar valores"
        assert view.text_toggle_hide_values.value == "Ocultar Valores"
        assert view.card_total_val.value == "R$ 120,00"
        mock_set_item.assert_called_with(mock_page, "mai_finance_hide_values", False)

    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_expenses_list_and_floating_bar_masked_when_hidden(self, mock_summary, mock_expenses):
        mock_expenses.return_value = [
            {"id": "exp-1", "description": "Supermercado", "amount": 450.0, "status": "pago", "due_date": "2026-09-08"},
            {"id": "exp-2", "description": "Farmácia", "amount": 85.0, "status": "pendente", "due_date": "2026-09-12"},
        ]
        mock_summary.return_value = {
            "total_despesas": 535.0,
            "total_pago": 450.0,
            "total_pendente": 85.0,
            "qtd_pendente": 1,
            "percent_pago": 84.1,
        }

        mock_page = MagicMock(spec=ft.Page)
        mock_page.width = 360  # Modo mobile compacto
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Ativa modo de privacidade
        view._toggle_hide_values()

        # Verifica que os valores dos cards de despesas na lista estão mascarados
        first_card = view.expenses_list_col.controls[0]
        # O amount_container está na primeira linha (top_row)
        top_row = first_card.content.controls[0]
        amount_text = top_row.controls[1].content.value
        assert amount_text == "R$ •••••"

        # Seleciona ambas as despesas e verifica a barra flutuante
        view._toggle_expense_selection("exp-1", True)
        view._toggle_expense_selection("exp-2", True)
        assert view.floating_selection_bar.visible is True
        assert view.selected_totals_sum_text.value == "R$ •••••"
        assert "R$ •••••" in view.subtotal_pago_text.value
        assert "R$ •••••" in view.subtotal_pendente_text.value

    @patch("ui.dashboard_view.get_previous_month_pending")
    @patch("ui.dashboard_view.list_expenses")
    @patch("ui.dashboard_view.get_monthly_summary")
    def test_prev_month_pending_modal_masked_when_hidden(self, mock_summary, mock_expenses, mock_pending):
        mock_expenses.return_value = []
        mock_summary.return_value = {"total_despesas": 0.0, "total_pago": 0.0, "total_pendente": 0.0, "qtd_pendente": 0, "percent_pago": 100.0}
        mock_pending.return_value = {
            "prev_month_ref": "2026-08",
            "items": [
                {
                    "id": "exp-p1",
                    "description": "Condomínio",
                    "amount": 380.0,
                    "due_date": "2026-08-10",
                    "category": {"name": "Moradia", "color": "#3B82F6"},
                }
            ],
            "count": 1,
            "total_amount": 380.0,
        }

        mock_page = MagicMock(spec=ft.Page)
        view = DashboardView(page=mock_page)
        view.load_data(silent=True)

        # Ativa ocultação e abre modal
        view._toggle_hide_values()
        view._open_prev_month_alert_modal()

        dlg = mock_page.show_dialog.call_args[0][0]
        header_text = dlg.content.content.controls[0].value
        assert "Total em aberto: R$ •••••" in header_text

        items_list = dlg.content.content.controls[1]
        row_item = items_list.controls[0]
        item_amt_text = row_item.content.controls[0].controls[1].value
        assert item_amt_text == "R$ •••••"






