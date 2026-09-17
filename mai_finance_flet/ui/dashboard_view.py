"""
dashboard_view.py — Tela Principal (Dashboard) do MAI Finance.

Implementa:
- Navegação mensal e seletor de competência (AC-005)
- Cards de resumo ampliados com monthly_summary e FinancialProgressRing (AC-006, AC-007)
- Alerta com badge e modal de pendências do mês anterior
- Barra de busca, filtro de status nivelado e botões de atalho
- Listagem responsiva: Cards no mobile (<768px) e Tabela completa no desktop (>=768px)
- Toggle instantâneo pago/pendente e edição inline rápida (AC-009)
- Modal para criação e edição de despesas compatível com Flet 1.0 (AC-008)
- Confirmação de exclusão com diálogo seguro (AC-008)
- Alternância completa de tema Dark/Light para toda a interface
- Polling periódico de 30 segundos como fallback para atualização reativa
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Callable
import flet as ft

from services.updater import check_for_updates, CURRENT_VERSION
from ui.components.update_modal import open_update_dialog

from services.categories import list_categories
from services.expenses import (
    list_expenses,
    get_monthly_summary,
    create_expense,
    update_expense,
    delete_expense,
    toggle_expense_status,
    get_previous_month_pending,
)
from ui.components.progress_ring import FinancialProgressRing
from ui.components.mai_loading import MaiLoading
from ui.components.modal_header import build_modal_header
from ui.nav import toggle_theme, get_current_theme
from ui.storage_util import get_local_item
from ui.theme import (
    get_tokens,
    get_badge_colors,
    format_brl,
    month_label,
    shift_month,
    get_current_month_ref,
    format_payment_date_to_ui,
)

class DashboardView(ft.Container):
    """View do Dashboard Principal de Gestão Financeira."""

    def __init__(
        self,
        page: ft.Page,
        on_logout: Callable[[], None] | None = None,
        on_open_categories: Callable[[], None] | None = None,
        on_open_clone_month: Callable[[], None] | None = None,
        on_open_backups: Callable[[], None] | None = None,
        on_open_import: Callable[[], None] | None = None,
        on_open_chat: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.page_ref = page
        self.on_logout = on_logout
        self.on_open_categories = on_open_categories
        self.on_open_clone_month = on_open_clone_month
        self.on_open_backups = on_open_backups
        self.on_open_import = on_open_import
        self.on_open_chat = on_open_chat

        self.expand = True
        self.bgcolor = "#08090F"

        # Detecção de responsividade segura (compatível com mocks e mobile-first)
        self.is_mobile = self._detect_mobile()
        self.is_compact = self._detect_compact()
        self.is_header_compact = self._detect_header_compact()
        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8) if self.is_mobile else ft.Padding.all(16)

        # Estado da view
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)
        self.current_month_ref = get_current_month_ref()
        self.expenses: list[dict[str, Any]] = []
        self.available_categories: list[dict[str, Any]] = []
        self.editing_cell: tuple[str, str] | None = None
        self.summary: dict[str, Any] = {
            "total_despesas": 0.0,
            "total_pago": 0.0,
            "total_pendente": 0.0,
            "qtd_pendente": 0,
            "percent_pago": 100.0,
        }
        self.prev_month_pending: dict[str, Any] = {
            "prev_month_ref": shift_month(self.current_month_ref, -1),
            "items": [],
            "count": 0,
            "total_amount": 0.0,
        }
        self.search_query = ""
        self.status_filter = "todos"
        self.is_loading = False
        self._polling_active = True

        # Usuário logado
        user_data_raw = get_local_item(page, "user_data") or {}
        if isinstance(user_data_raw, str):
            try:
                user_data = json.loads(user_data_raw)
            except Exception:
                user_data = {}
        elif isinstance(user_data_raw, dict):
            user_data = user_data_raw
        else:
            user_data = {}
        self.user_name = user_data.get("name", "Usuário")
        self.user_email = user_data.get("email", "")

        # Inicializa sub-componentes visuais
        self._init_ui()

    def _get_current_width(self, event_width: float | None = None) -> float:
        if event_width is not None and isinstance(event_width, (int, float)) and event_width > 0:
            return float(event_width)
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)) and raw_w > 0:
                return float(raw_w)
        except Exception:
            pass
        # Mobile-first: se a largura ainda não foi sincronizada pelo cliente/navegador
        plat = str(getattr(self.page_ref, "platform", "")).lower()
        ua = str(getattr(self.page_ref, "client_user_agent", "")).lower()
        if "android" in plat or "ios" in plat or "mobile" in ua or "android" in ua or "iphone" in ua:
            return 360.0
        # Em web antes do handshake, se for desconhecido, usamos 400.0 para que nasça mobile e nunca quebre
        return 400.0

    def _detect_mobile(self, event_width: float | None = None) -> bool:
        return self._get_current_width(event_width) < 768

    def _detect_compact(self, event_width: float | None = None) -> bool:
        return self._get_current_width(event_width) < 1024

    def _detect_header_compact(self, event_width: float | None = None) -> bool:
        """Usa cabeçalho em 2 linhas para telas mobile (< 768px), protegendo o botão de Sair/Logout."""
        return self._detect_mobile(event_width)

    def _init_ui(self) -> None:
        # Header: Logo, Usuário, Seletor de Mês, Alerta, Tema e Logout
        self.header_title = ft.Text("MAI Finance", size=18, weight=ft.FontWeight.BOLD, color=self.T["accent"], no_wrap=True)
        self.header_user = ft.Text(f"Olá, {self.user_name}", size=12, color=self.T["textMuted"], no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)

        self.logo_icon = ft.Image(src="logo.png", width=32, height=32, fit=ft.BoxFit.CONTAIN)
        self.logo_user_row = ft.Row(
            [
                self.logo_icon,
                ft.Column([self.header_title, self.header_user], spacing=0),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )

        # Seletor de Mês Integrado no Topo: < Mês AAAA > [Hoje]
        self.month_display = ft.Text(
            month_label(self.current_month_ref),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.T["textPrimary"],
        )
        self.btn_prev_month = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=self.T["accent"],
            icon_size=20,
            tooltip="Mês Anterior",
            on_click=lambda _: self._change_month(-1),
        )
        self.btn_next_month = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=self.T["accent"],
            icon_size=20,
            tooltip="Próximo Mês",
            on_click=lambda _: self._change_month(1),
        )
        self.btn_current_month = ft.Button(
            content=ft.Text("Mês Atual", size=11, color=self.T["accent"]),
            style=ft.ButtonStyle(
                bgcolor=self.T["surfaceSolid"],
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            height=30,
            on_click=lambda _: self._reset_to_current_month(),
        )

        self.month_selector_box = ft.Container(
            content=ft.Row(
                [self.btn_prev_month, self.month_display, self.btn_next_month, self.btn_current_month],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            bgcolor=self.T["surfaceSolid"],
            border_radius=8,
            border=ft.Border.all(1, self.T["border"]),
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        # Ícone de Alerta de Pendências do Mês Anterior com Badge
        self.alert_badge_text = ft.Text("0", size=10, weight=ft.FontWeight.BOLD, color="#08090F")
        self.alert_badge = ft.Container(
            content=self.alert_badge_text,
            bgcolor=self.T["warning"],
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
            visible=False,
            on_click=lambda _: self._open_prev_month_alert_modal(),
        )
        self.btn_alert_icon = ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            tooltip="Pendências do Mês Anterior",
            icon_color=self.T["textMuted"],
            icon_size=20,
            on_click=lambda _: self._open_prev_month_alert_modal(),
        )
        self.btn_alert_box = ft.Container(
            content=ft.Stack(
                [
                    self.btn_alert_icon,
                    ft.Container(
                        content=self.alert_badge,
                        alignment=ft.Alignment.TOP_RIGHT,
                        padding=ft.Padding.only(top=2, right=2),
                        on_click=lambda _: self._open_prev_month_alert_modal(),
                    ),
                ],
                width=36,
                height=36,
            ),
            tooltip="Pendências do Mês Anterior",
            on_click=lambda _: self._open_prev_month_alert_modal(),
        )

        self.btn_theme = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE_OUTLINED if self.theme_mode == "dark" else ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Alternar Tema Claro/Escuro",
            icon_color=self.T["accent"],
            icon_size=20,
            on_click=self._handle_toggle_theme,
        )

        self.btn_logout = ft.IconButton(
            icon=ft.Icons.LOGOUT,
            tooltip="Sair da Conta",
            icon_color=self.T["danger"],
            icon_size=20,
            on_click=lambda _: self.on_logout() if self.on_logout else None,
        )

        self.btn_check_update = ft.IconButton(
            icon=ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED,
            tooltip="Verificar Atualizações",
            icon_color=self.T["textMuted"],
            icon_size=20,
            on_click=lambda _: self._manual_check_update(),
        )

        self.account_row = ft.Row(
            [self.btn_check_update, self.btn_alert_box, self.btn_theme, self.btn_logout],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )

        # Header desktop (linha única para telas amplas >= 900px)
        self.header_row = ft.Row(
            [self.logo_user_row, self.month_selector_box, self.account_row],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Header mobile / compacto (duas linhas para telas < 900px: 1) Logo + Conta sem corte, 2) Seletor Mês centralizado)
        self.header_mobile_col = ft.Column(
            [
                ft.Row(
                    [self.logo_user_row, self.account_row],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [self.month_selector_box],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        )

        self.header_container = ft.Container(
            content=self.header_mobile_col if self.is_header_compact else self.header_row
        )

        # Cards de Resumo Mensal Espaçosos e Proeminentes (Métricas Modernas)
        self.card_total_title = ft.Text("TOTAL DESPESAS", size=11, weight=ft.FontWeight.W_600, color=self.T["textMuted"])
        self.card_total_val = ft.Text(format_brl(0.0), size=18, weight=ft.FontWeight.BOLD, color=self.T["accent"])
        self.card_total_icon = ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=18, color=self.T["accent"])
        self.card_total = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.card_total_icon, self.card_total_title], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.card_total_val,
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["border"]),
            border_radius=10,
            padding=ft.Padding.all(12),
            expand=True,
        )

        self.card_pago_title = ft.Text("TOTAL PAGO", size=11, weight=ft.FontWeight.W_600, color=self.T["textMuted"])
        self.card_pago_val = ft.Text(format_brl(0.0), size=18, weight=ft.FontWeight.BOLD, color=self.T["success"])
        self.card_pago_icon = ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=18, color=self.T["success"])
        self.progress_ring = FinancialProgressRing(
            pct=100.0,
            size=34,
            stroke_width=3.5,
            color=self.T.get("ring1", self.T["success"]),
            bgcolor=self.T.get("ringTrack", self.T["borderSubtle"]),
            text_color=self.T.get("textPrimary", "#F1F5F9"),
        )
        self.card_pago = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row([self.card_pago_icon, self.card_pago_title], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            self.card_pago_val,
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True,
                    ),
                    self.progress_ring,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["border"]),
            border_radius=10,
            padding=ft.Padding.all(12),
            expand=True,
        )

        self.card_pendente_title = ft.Text("A PAGAR", size=11, weight=ft.FontWeight.W_600, color=self.T["textMuted"])
        self.card_pendente_val = ft.Text(format_brl(0.0), size=18, weight=ft.FontWeight.BOLD, color=self.T["warning"])
        self.card_pendente_icon = ft.Icon(ft.Icons.SCHEDULE, size=18, color=self.T["warning"])
        self.card_pendente_badge = ft.Text("0 pendências", size=11, color=self.T["warning"])
        self.card_pendente = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self.card_pendente_icon,
                            self.card_pendente_title,
                            ft.Text("•", size=11, color=self.T["border"]),
                            self.card_pendente_badge,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.card_pendente_val,
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["border"]),
            border_radius=10,
            padding=ft.Padding.all(12),
            expand=True,
        )

        self.summary_bar = self._build_summary_bar()

        # Botão de limpar busca rápida
        self.btn_clear_search = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=self.T["textMuted"],
            tooltip="Limpar busca",
            visible=False,
            on_click=lambda _: self._clear_search(),
        )

        # Barra Unificada: Busca + Filtro Status Nivelado + Nova Despesa + Ações Limpas
        self.search_field = ft.TextField(
            hint_text="Buscar despesa...",
            prefix_icon=ft.Icons.SEARCH,
            suffix=self.btn_clear_search,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            height=38,
            width=None if self.is_compact else 220,
            expand=True if self.is_compact else False,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
            text_size=13,
            on_change=self._on_search_change,
        )

        # Banner informativo de filtros ativos com botão Limpar
        self.active_filter_text = ft.Text("", size=11, weight=ft.FontWeight.W_600, color=self.T["warning"])
        self.btn_clear_all_filters = ft.Button(
            content=ft.Row(
                [
                    ft.Text("Limpar filtros", size=11, weight=ft.FontWeight.BOLD, color="#08090F"),
                    ft.Icon(ft.Icons.CLOSE, size=12, color="#08090F"),
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["warning"],
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
            height=26,
            on_click=lambda _: self._clear_all_filters(),
        )
        self.active_filters_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.FILTER_LIST, size=14, color=self.T["warning"]),
                            self.active_filter_text,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    self.btn_clear_all_filters,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T["warningBg"],
            border=ft.Border.all(1, self.T["warningBorder"]),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            visible=False,
        )

        status_init_label = "Todos" if self.is_compact else "Todos os status"
        self.filter_status_text = ft.Text(status_init_label, size=12, color=self.T["textPrimary"])
        self.filter_status_icon = ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=18, color=self.T["textMuted"])
        self.filter_dropdown_container = ft.Container(
            content=ft.Row(
                [self.filter_status_text, self.filter_status_icon],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            height=38,
            width=120 if self.is_compact else 165,
            padding=ft.Padding.symmetric(horizontal=6 if self.is_compact else 10, vertical=0),
            alignment=ft.Alignment.CENTER,
        )

        self.filter_dropdown = ft.PopupMenuButton(
            content=self.filter_dropdown_container,
            padding=0,
            tooltip="Filtrar por status",
            items=[
                ft.PopupMenuItem(content=ft.Text("Todos os status", size=13), on_click=lambda _: self._on_status_filter_selected("todos")),
                ft.PopupMenuItem(content=ft.Text("Pendentes", size=13), on_click=lambda _: self._on_status_filter_selected("pendente")),
                ft.PopupMenuItem(content=ft.Text("Pagos", size=13), on_click=lambda _: self._on_status_filter_selected("pago")),
            ],
        )
        self.filter_dropdown.value = "todos"

        self.btn_nova_despesa = ft.Button(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD, size=16, color="#08090F"), ft.Text("Nova Despesa", size=12, weight=ft.FontWeight.BOLD, color="#08090F")],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            ),
            height=38,
            visible=not self.is_mobile,
            on_click=lambda _: self._open_expense_dialog(),
        )

        self.btn_categorias = self._build_action_button("Categorias", ft.Icons.LABEL_OUTLINED, self.on_open_categories)
        self.btn_clonar = self._build_action_button("Clonar Mês", ft.Icons.COPY_ALL_OUTLINED, self.on_open_clone_month)
        self.btn_backups = self._build_action_button("Backups", ft.Icons.BACKUP_OUTLINED, self.on_open_backups)

        self.btn_categorias.visible = not self.is_compact
        self.btn_clonar.visible = not self.is_compact
        self.btn_backups.visible = not self.is_compact

        self.btn_more_options = ft.PopupMenuButton(
            content=ft.Container(
                content=ft.Icon(ft.Icons.MORE_VERT, size=20, color=self.T["textPrimary"]),
                bgcolor=self.T["surfaceSolid"],
                border=ft.Border.all(1, self.T["borderSubtle"]),
                border_radius=8,
                width=38,
                height=38,
                alignment=ft.Alignment.CENTER,
            ),
            padding=0,
            tooltip="Mais Ações (Nova Despesa, Clonar, Backups, Categorias)",
            items=[
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=self.T["accent"]), ft.Text("Nova Despesa", size=13, weight=ft.FontWeight.BOLD)]),
                    on_click=lambda _: self._open_expense_dialog(),
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.LABEL_OUTLINED, size=18, color=self.T["textPrimary"]), ft.Text("Categorias", size=13)]),
                    on_click=lambda _: self.on_open_categories() if self.on_open_categories else None,
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.COPY_ALL_OUTLINED, size=18, color=self.T["textPrimary"]), ft.Text("Clonar Mês", size=13)]),
                    on_click=lambda _: self.on_open_clone_month() if self.on_open_clone_month else None,
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.BACKUP_OUTLINED, size=18, color=self.T["textPrimary"]), ft.Text("Backups", size=13)]),
                    on_click=lambda _: self.on_open_backups() if self.on_open_backups else None,
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED, size=18, color=self.T["accent"]), ft.Text("Verificar Atualizações", size=13)]),
                    on_click=lambda _: self._manual_check_update(),
                ),
            ],
            visible=self.is_compact,
        )

        self.action_filter_bar = ft.Row(
            [
                self.search_field,
                self.filter_dropdown,
                self.btn_nova_despesa,
                self.btn_categorias,
                self.btn_clonar,
                self.btn_backups,
                self.btn_more_options,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Área da Lista de Despesas
        self.expenses_list_col = ft.Column(spacing=6, expand=True, scroll=ft.ScrollMode.AUTO)
        self.loading_ring = ft.Container(
            content=MaiLoading(message="Carregando despesas...", size=44),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.all(40),
            visible=False,
        )
        self.empty_msg = ft.Text("Nenhuma despesa encontrada para este período.", size=14, color=self.T["textMuted"], text_align=ft.TextAlign.CENTER)
        self.btn_empty_clear_filters = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FILTER_ALT_OFF, size=15, color="#08090F"),
                    ft.Text("Limpar filtros e ver todas", size=12, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["warning"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            ),
            height=32,
            visible=False,
            on_click=lambda _: self._clear_all_filters(),
        )
        self.empty_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=48, color=self.T["textMuted"]),
                    self.empty_msg,
                    self.btn_empty_clear_filters,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.all(40),
            visible=False,
        )

        # Cabeçalho da Tabela (Desktop Amplo >= 1024px)
        header_text_color = self.T.get("textHeader", self.T["textMuted"])
        self.table_header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=ft.Text("VENC.", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, no_wrap=True), width=65),
                    ft.Container(content=ft.Text("CATEGORIA", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, no_wrap=True), width=120),
                    ft.Container(content=ft.Text("DESCRIÇÃO", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, no_wrap=True), expand=3),
                    ft.Container(content=ft.Text("VALOR", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, text_align=ft.TextAlign.RIGHT, no_wrap=True), width=105, alignment=ft.Alignment.CENTER_RIGHT),
                    ft.Container(content=ft.Text("PAGTO", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, text_align=ft.TextAlign.CENTER, no_wrap=True), width=70, alignment=ft.Alignment.CENTER),
                    ft.Container(content=ft.Text("STATUS", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, text_align=ft.TextAlign.CENTER, no_wrap=True), width=90, alignment=ft.Alignment.CENTER),
                    ft.Container(content=ft.Text("OBSERVAÇÃO", size=11, weight=ft.FontWeight.BOLD, color=header_text_color, no_wrap=True), expand=2),
                    ft.Container(width=105),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T.get("tableHeaderBg", self.T["surfaceSolid"]),
            border=ft.Border.all(1, self.T.get("tableHeaderBorder", self.T["borderSubtle"])),
            border_radius=8,
            padding=ft.Padding.only(left=12, right=14, top=8, bottom=8),
            visible=not self.is_compact,
        )

        self.divider = ft.Divider(color=self.T["borderSubtle"], height=1)

        # Montagem do Layout Principal
        self.content = ft.Column(
            [
                self.header_container,
                self.divider,
                self.summary_bar,
                self.action_filter_bar,
                self.active_filters_banner,
                self.table_header,
                self.loading_ring,
                self.empty_container,
                self.expenses_list_col,
            ],
            spacing=10,
            expand=True,
        )

        self._apply_theme()
        self._update_fab()

    def _build_summary_bar(self) -> ft.Control:
        if self.is_mobile:
            self.card_total.expand = False
            self.card_pago.expand = True
            self.card_pendente.expand = True
            tier2_row = ft.Row(
                [self.card_pago, self.card_pendente],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return ft.Column(
                [self.card_total, tier2_row],
                spacing=8,
            )
        else:
            self.card_total.expand = True
            self.card_pago.expand = True
            self.card_pendente.expand = True
            return ft.Row(
                [self.card_total, self.card_pago, self.card_pendente],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

    def _build_action_button(self, label: str, icon: str, on_click: Callable[[], None] | None) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            tooltip=label,
            icon_color=self.T["textPrimary"],
            icon_size=18,
            style=ft.ButtonStyle(
                bgcolor=self.T["surfaceSolid"],
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, self.T["borderSubtle"]),
            ),
            width=38,
            height=38,
            on_click=lambda _: on_click() if on_click else None,
        )

    def _update_fab(self) -> None:
        if hasattr(self.page_ref, "floating_action_button"):
            if self.is_mobile:
                self.page_ref.floating_action_button = ft.FloatingActionButton(
                    icon=ft.Icons.ADD,
                    bgcolor=self.T["accent"],
                    foreground_color=self.T.get("accentOnBrand", "#08090F"),
                    tooltip="Nova Despesa",
                    on_click=lambda _: self._open_expense_dialog(),
                )
            else:
                self.page_ref.floating_action_button = None

    def _update_filter_status_label(self) -> None:
        labels = {
            "todos": "Todos" if self.is_compact else "Todos os status",
            "pendente": "Pendentes",
            "pago": "Pagos",
        }
        if hasattr(self, "filter_status_text"):
            self.filter_status_text.value = labels.get(self.status_filter, "Todos" if self.is_compact else "Todos os status")

    # -----------------------------------------------------------------------
    # Ciclo de Vida e Responsividade
    # -----------------------------------------------------------------------
    def did_mount(self) -> None:
        self._update_fab()
        if hasattr(self.page_ref, "on_resize"):
            self.page_ref.on_resize = self._handle_page_resized
        elif hasattr(self.page_ref, "on_resized"):
            self.page_ref.on_resized = self._handle_page_resized
        self._handle_page_resized()
        self.load_data()
        if hasattr(self.page_ref, "run_task"):
            self.page_ref.run_task(self._start_polling)

        # Checagem em segundo plano de nova versão do aplicativo
        threading.Thread(target=self._check_update_silently, daemon=True).start()

    def will_unmount(self) -> None:
        self._polling_active = False
        if hasattr(self.page_ref, "floating_action_button"):
            self.page_ref.floating_action_button = None

    def _handle_page_resized(self, e: Any = None) -> None:
        event_w = getattr(e, "width", None) if e is not None else None
        new_mobile = self._detect_mobile(event_w)
        new_compact = self._detect_compact(event_w)
        new_header_compact = self._detect_header_compact(event_w)

        # Otimização: detecta se houve transição de breakpoint
        has_mounted = getattr(self, "_has_resized_once", False)
        state_changed = (
            not has_mounted
            or (new_mobile != self.is_mobile)
            or (new_compact != self.is_compact)
            or (new_header_compact != self.is_header_compact)
        )
        self._has_resized_once = True

        self.is_mobile = new_mobile
        self.is_compact = new_compact
        self.is_header_compact = new_header_compact

        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8) if self.is_mobile else ft.Padding.all(16)
        self.header_user.visible = not self.is_mobile
        self.header_container.content = self.header_mobile_col if self.is_header_compact else self.header_row

        # Ajusta busca e filtro de status
        self.search_field.width = None if self.is_compact else 220
        self.search_field.expand = True if self.is_compact else False
        self.filter_dropdown_container.width = 120 if self.is_compact else 165
        self.filter_dropdown_container.padding = ft.Padding.symmetric(horizontal=6 if self.is_compact else 10, vertical=0)
        self._update_filter_status_label()

        # Ajusta botões de ação e FAB
        self.btn_nova_despesa.visible = not self.is_mobile
        self.btn_categorias.visible = not self.is_compact
        self.btn_clonar.visible = not self.is_compact
        self.btn_backups.visible = not self.is_compact
        self.btn_more_options.visible = self.is_compact
        self._update_fab()

        # Ajusta tabela e resumo
        self.table_header.visible = not self.is_compact
        new_summary = self._build_summary_bar()
        try:
            idx = self.content.controls.index(self.summary_bar)
            self.content.controls[idx] = new_summary
            self.summary_bar = new_summary
        except ValueError:
            pass

        # Apenas re-renderiza toda a lista de despesas se os breakpoints mudaram
        if state_changed:
            self._render_expenses_list()
        try:
            self.page_ref.update()
        except Exception:
            pass

    async def _start_polling(self) -> None:
        while self._polling_active:
            await asyncio.sleep(30)
            if self._polling_active:
                self.load_data(silent=True)

    def load_data(self, silent: bool = False) -> None:
        """Carrega lista de despesas, resumo do mês, pendências do mês anterior e categorias."""
        if not silent:
            self.loading_ring.visible = True
            self.expenses_list_col.visible = False
            self.empty_container.visible = False
            self.page_ref.update()

        try:
            self.expenses = list_expenses(self.current_month_ref)
            self.summary = get_monthly_summary(self.current_month_ref)
        except Exception as exc:
            print(f"[load_data] Erro ao carregar despesas/resumo: {exc}")
            self.expenses = []
            self.summary = {
                "total_despesas": 0.0,
                "total_pago": 0.0,
                "total_pendente": 0.0,
                "qtd_pendente": 0,
                "percent_pago": 100.0,
            }

        try:
            self.available_categories = list_categories()
        except Exception as exc:
            print(f"[load_data] Erro ao carregar categorias: {exc}")
            self.available_categories = []

        try:
            self.prev_month_pending = get_previous_month_pending(self.current_month_ref)
        except Exception as exc:
            print(f"[load_data] Erro ao carregar pendências do mês anterior: {exc}")
            self.prev_month_pending = {
                "prev_month_ref": shift_month(self.current_month_ref, -1),
                "items": [],
                "count": 0,
                "total_amount": 0.0,
            }

        self._update_summary_ui()
        self._render_expenses_list()

        self.loading_ring.visible = False
        self.expenses_list_col.visible = True
        self.page_ref.update()

    def _update_summary_ui(self) -> None:
        self.card_total_val.value = format_brl(self.summary.get("total_despesas", 0.0))
        self.card_pago_val.value = format_brl(self.summary.get("total_pago", 0.0))
        self.card_pendente_val.value = format_brl(self.summary.get("total_pendente", 0.0))
        qtd = self.summary.get("qtd_pendente", 0)
        self.card_pendente_badge.value = f"{qtd} pendência{'s' if qtd != 1 else ''}"
        self.progress_ring.set_pct(self.summary.get("percent_pago", 100.0))

        # Atualiza badge e tooltip de pendências do mês anterior
        prev_cnt = self.prev_month_pending.get("count", 0)
        prev_ref = self.prev_month_pending.get("prev_month_ref", "")
        if prev_cnt > 0:
            self.alert_badge_text.value = str(prev_cnt)
            self.alert_badge.visible = True
            self.btn_alert_icon.icon = ft.Icons.NOTIFICATIONS_ACTIVE
            self.btn_alert_icon.icon_color = self.T["warning"]
            self.btn_alert_icon.tooltip = f"{prev_cnt} despesa(s) pendente(s) em {month_label(prev_ref)}"
        else:
            self.alert_badge.visible = False
            self.btn_alert_icon.icon = ft.Icons.NOTIFICATIONS_OUTLINED
            self.btn_alert_icon.icon_color = self.T["textMuted"]
            self.btn_alert_icon.tooltip = f"Nenhuma pendência em {month_label(prev_ref)}"

    def _start_inline_edit(self, expense_id: str, field: str) -> None:
        self.editing_cell = (str(expense_id), field)
        self._render_expenses_list()
        self.page_ref.update()

    def _cancel_inline_edit(self) -> None:
        self.editing_cell = None
        self._render_expenses_list()
        self.page_ref.update()

    def _commit_inline_edit(self, expense_id: str, field: str, new_value: str) -> None:
        val = (new_value or "").strip()
        patch: dict[str, Any] = {}

        try:
            if field == "description":
                if not val:
                    self._show_snack("A descrição não pode ser vazia.", is_error=True)
                    return
                patch["description"] = val

            elif field == "amount":
                cleaned = val.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                val_num = float(cleaned)
                if val_num < 0:
                    raise ValueError
                patch["amount"] = val_num

            elif field == "due_date":
                if val.isdigit() and 1 <= int(val) <= 31:
                    patch["due_date"] = f"{self.current_month_ref}-{int(val):02d}"
                elif len(val) == 10 and val[4] == "-" and val[7] == "-":
                    patch["due_date"] = val
                    patch["month_ref"] = f"{val[:7]}-01"
                else:
                    self._show_snack("Informe o dia (ex: 10) ou data AAAA-MM-DD.", is_error=True)
                    return

            elif field == "payment_date":
                if not val or val == "-":
                    patch["payment_date"] = None
                    patch["status"] = "pendente"
                else:
                    patch["payment_date"] = val
                    patch["status"] = "pago"

            elif field == "observation":
                patch["observation"] = val if val else None

            update_expense(expense_id, patch)
            self.editing_cell = None
            self.load_data(silent=True)
            self._show_snack("Lançamento atualizado!")
        except Exception as exc:
            self._show_snack(f"Erro ao atualizar: {exc}", is_error=True)

    def _render_expenses_list(self) -> None:
        self.expenses_list_col.controls.clear()
        self._update_active_filters_banner()

        # Filtra por texto de busca e status
        filtered = []
        for exp in self.expenses:
            if self.status_filter != "todos" and exp.get("status") != self.status_filter:
                continue

            if self.search_query:
                q = self.search_query.lower()
                desc = (exp.get("description") or "").lower()
                obs = (exp.get("observation") or "").lower()
                if q not in desc and q not in obs:
                    continue

            filtered.append(exp)

        if not filtered:
            has_filters = bool(self.search_query.strip()) or (self.status_filter != "todos")
            if hasattr(self, "empty_msg"):
                if has_filters:
                    self.empty_msg.value = "Nenhuma despesa encontrada com os filtros aplicados."
                    if hasattr(self, "btn_empty_clear_filters"):
                        self.btn_empty_clear_filters.visible = True
                else:
                    self.empty_msg.value = "Nenhuma despesa encontrada para este período."
                    if hasattr(self, "btn_empty_clear_filters"):
                        self.btn_empty_clear_filters.visible = False
            self.empty_container.visible = True
            return

        self.empty_container.visible = False

        for exp in filtered:
            if self.is_compact:
                item = self._build_expense_mobile_card(exp)
            else:
                item = self._build_expense_row(exp)
            self.expenses_list_col.controls.append(item)

    # -----------------------------------------------------------------------
    # Cards Mobile / Compacto (< 1024px)
    # -----------------------------------------------------------------------
    def _build_expense_mobile_card(self, exp: dict[str, Any]) -> ft.Container:
        exp_id = str(exp.get("id", ""))
        status = exp.get("status", "pendente")
        is_pago = status == "pago"
        description = exp.get("description", "")
        amount = float(exp.get("amount") or 0.0)
        due_date = exp.get("due_date", "")
        payment_date = exp.get("payment_date")
        obs = exp.get("observation") or ""

        cat_info = exp.get("category") or {}
        cat_name = cat_info.get("name") if isinstance(cat_info, dict) else "Outros"
        if not cat_name:
            cat_name = "Outros"
        cat_color = (cat_info.get("color") or cat_info.get("color_hex") if isinstance(cat_info, dict) else None) or "#94A3B8"

        due_day = due_date.split("-")[-1] if "-" in due_date else due_date
        due_display = f"{due_day}/{due_date.split('-')[-2]}" if "-" in due_date else due_date

        venc_badge = ft.Container(
            content=ft.Text(f"Venc. {due_display}", size=11, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
            bgcolor=self.T["pageBg"],
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            tooltip="Clique para alterar vencimento",
            on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "due_date"),
        )

        cat_bg, cat_fg, cat_border = get_badge_colors(cat_color, is_light=self.theme_mode == "light")
        cat_badge = ft.Container(
            content=ft.Text(cat_name, size=11, weight=ft.FontWeight.W_600, color=cat_fg),
            bgcolor=cat_bg,
            border=ft.Border.all(1, cat_border) if cat_border else None,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        amount_container = ft.Container(
            content=ft.Text(format_brl(amount), size=15, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"]),
            tooltip="Clique para alterar valor",
            on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "amount"),
        )

        top_row = ft.Row(
            [ft.Row([venc_badge, cat_badge], spacing=6), amount_container],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        desc_text = ft.Text(
            description,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.T["textPrimary"] if not is_pago else self.T["textMuted"],
            expand=True,
        )

        obs_box: ft.Container | None = None
        obs_badge: ft.Container | None = None

        if obs:
            obs_box = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.NOTES, size=13, color=self.T["accent"]),
                        ft.Text(obs, size=11, color=self.T["textMuted"], italic=True, expand=True),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor=self.T["pageBg"],
                border=ft.Border.all(1, self.T["borderSubtle"]),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                visible=False,
            )

            def toggle_obs(e, target_box=obs_box):
                target_box.visible = not target_box.visible
                try:
                    target_box.update()
                except Exception:
                    try:
                        if self.page_ref:
                            self.page_ref.update()
                    except Exception:
                        pass

            obs_box.on_click = toggle_obs

            obs_badge = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.NOTES, size=12, color=self.T["accent"]),
                        ft.Text("Obs", size=10, weight=ft.FontWeight.W_600, color=self.T["accent"]),
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=self.T["pageBg"],
                border=ft.Border.all(1, self.T["borderSubtle"]),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                tooltip="Toque para ver a observação desta despesa",
                on_click=toggle_obs,
                ink=True,
            )

        def on_desc_click(e):
            if obs_box:
                toggle_obs(e)
            else:
                self._start_inline_edit(exp_id, "description")

        desc_container = ft.Container(
            content=desc_text,
            tooltip="Toque para ver a observação" if obs else "Clique para alterar descrição",
            on_click=on_desc_click,
            expand=True,
        )

        if obs_badge:
            desc_row = ft.Row(
                [desc_container, obs_badge],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            )
        else:
            desc_row = desc_container

        btn_status_toggle = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_pago else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        size=16,
                        color=self.T["success"] if is_pago else self.T["warning"],
                    ),
                    ft.Text(
                        f"Pago ({format_payment_date_to_ui(payment_date)})" if (is_pago and payment_date) else ("Pago" if is_pago else "Pendente"),
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=self.T["success"] if is_pago else self.T["warning"],
                    ),
                ],
                spacing=4,
            ),
            bgcolor=self.T["successBg"] if is_pago else self.T["warningBg"],
            border=ft.Border.all(1, self.T["successBorder"] if is_pago else self.T["warningBorder"]),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            on_click=lambda _, eid=exp_id, st=status: self._toggle_status(eid, st),
            tooltip="Alternar status pago/pendente",
        )

        btn_duplicate = ft.IconButton(
            icon=ft.Icons.COPY_ALL_OUTLINED,
            icon_color=self.T["accent"],
            icon_size=18,
            width=32,
            height=32,
            padding=0,
            tooltip="Duplicar despesa",
            on_click=lambda _, item=exp: self._open_expense_dialog(item, is_duplicate=True),
        )
        btn_edit = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_color=self.T["textMuted"],
            icon_size=18,
            width=32,
            height=32,
            padding=0,
            tooltip="Editar completo",
            on_click=lambda _, item=exp: self._open_expense_dialog(item),
        )
        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=self.T["danger"],
            icon_size=18,
            width=32,
            height=32,
            padding=0,
            tooltip="Excluir",
            on_click=lambda _, eid=exp_id, d=description: self._confirm_delete(eid, d),
        )

        action_btns = ft.Row(
            [btn_duplicate, btn_edit, btn_delete],
            spacing=0,
            tight=True,
        )

        bottom_row = ft.Row(
            [btn_status_toggle, action_btns],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        card_controls: list[ft.Control] = [top_row, desc_row]
        if obs_box:
            card_controls.append(obs_box)
        card_controls.append(bottom_row)

        return ft.Container(
            content=ft.Column(card_controls, spacing=6),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=10,
            padding=ft.Padding.all(10),
        )

    # -----------------------------------------------------------------------
    # Tabela Desktop (>= 768px)
    # -----------------------------------------------------------------------
    def _build_expense_row(self, exp: dict[str, Any]) -> ft.Container:
        exp_id = str(exp.get("id", ""))
        status = exp.get("status", "pendente")
        is_pago = status == "pago"
        description = exp.get("description", "")
        amount = float(exp.get("amount") or 0.0)
        due_date = exp.get("due_date", "")
        payment_date = exp.get("payment_date")
        obs = exp.get("observation") or ""

        cat_info = exp.get("category") or {}
        cat_name = cat_info.get("name") if isinstance(cat_info, dict) else "Outros"
        if not cat_name:
            cat_name = "Outros"
        cat_color = (cat_info.get("color") or cat_info.get("color_hex") if isinstance(cat_info, dict) else None) or "#94A3B8"

        due_day = due_date.split("-")[-1] if "-" in due_date else due_date
        due_display = f"{due_day}/{due_date.split('-')[-2]}" if "-" in due_date else due_date

        # 1. Coluna Vencimento
        if self.editing_cell == (exp_id, "due_date"):
            input_due = ft.TextField(
                value=due_day,
                width=55,
                height=32,
                text_size=12,
                content_padding=ft.Padding.symmetric(horizontal=4, vertical=0),
                autofocus=True,
                on_submit=lambda e, eid=exp_id: self._commit_inline_edit(eid, "due_date", e.control.value),
            )
            col_due = ft.Row(
                [
                    input_due,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=14, icon_color=self.T["success"], on_click=lambda _, eid=exp_id: self._commit_inline_edit(eid, "due_date", input_due.value)),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14, icon_color=self.T["danger"], on_click=lambda _: self._cancel_inline_edit()),
                ],
                spacing=0,
                width=80,
            )
        else:
            col_due = ft.Container(
                content=ft.Text(due_display, size=12, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                width=65,
                tooltip="Clique para alterar vencimento",
                on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "due_date"),
            )

        # 2. Coluna Categoria
        cat_bg, cat_fg, cat_border = get_badge_colors(cat_color, is_light=self.theme_mode == "light")
        category_badge = ft.Container(
            content=ft.Text(cat_name, size=11, weight=ft.FontWeight.W_600, color=cat_fg),
            bgcolor=cat_bg,
            border=ft.Border.all(1, cat_border) if cat_border else None,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            tooltip=f"Categoria: {cat_name}",
        )
        col_cat = ft.Container(content=category_badge, width=120)

        # 3. Coluna Descrição
        if self.editing_cell == (exp_id, "description"):
            input_desc = ft.TextField(
                value=description,
                expand=True,
                height=32,
                text_size=13,
                content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
                autofocus=True,
                on_submit=lambda e, eid=exp_id: self._commit_inline_edit(eid, "description", e.control.value),
            )
            col_desc = ft.Row(
                [
                    input_desc,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=16, icon_color=self.T["success"], on_click=lambda _, eid=exp_id: self._commit_inline_edit(eid, "description", input_desc.value)),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=16, icon_color=self.T["danger"], on_click=lambda _: self._cancel_inline_edit()),
                ],
                spacing=2,
                expand=3,
            )
        else:
            col_desc = ft.Container(
                content=ft.Text(
                    description,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=self.T["textPrimary"] if not is_pago else self.T["textMuted"],
                    overflow=ft.TextOverflow.ELLIPSIS,
                    no_wrap=True,
                ),
                expand=3,
                tooltip="Clique para editar a descrição",
                on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "description"),
            )

        # 4. Coluna Valor
        if self.editing_cell == (exp_id, "amount"):
            input_amount = ft.TextField(
                value=f"{amount:.2f}".replace(".", ","),
                width=80,
                height=32,
                text_size=12,
                content_padding=ft.Padding.symmetric(horizontal=4, vertical=0),
                autofocus=True,
                on_submit=lambda e, eid=exp_id: self._commit_inline_edit(eid, "amount", e.control.value),
            )
            col_amount = ft.Row(
                [
                    input_amount,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=14, icon_color=self.T["success"], on_click=lambda _, eid=exp_id: self._commit_inline_edit(eid, "amount", input_amount.value)),
                ],
                spacing=0,
                width=105,
                alignment=ft.MainAxisAlignment.END,
            )
        else:
            col_amount = ft.Container(
                content=ft.Text(
                    format_brl(amount),
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=self.T["textPrimary"],
                    text_align=ft.TextAlign.RIGHT,
                ),
                width=105,
                alignment=ft.Alignment.CENTER_RIGHT,
                tooltip="Clique para alterar valor",
                on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "amount"),
            )

        # 5. Coluna Pagamento
        if self.editing_cell == (exp_id, "payment_date"):
            input_pay = ft.TextField(
                value=payment_date or "",
                width=65,
                height=32,
                text_size=11,
                content_padding=ft.Padding.symmetric(horizontal=4, vertical=0),
                autofocus=True,
                on_submit=lambda e, eid=exp_id: self._commit_inline_edit(eid, "payment_date", e.control.value),
            )
            col_payment = ft.Row(
                [
                    input_pay,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=14, icon_color=self.T["success"], on_click=lambda _, eid=exp_id: self._commit_inline_edit(eid, "payment_date", input_pay.value)),
                ],
                spacing=0,
                width=70,
            )
        else:
            col_payment = ft.Container(
                content=ft.Text(
                    format_payment_date_to_ui(payment_date) if is_pago else "-",
                    size=11,
                    color=self.T["textMuted"],
                    text_align=ft.TextAlign.CENTER,
                ),
                width=70,
                alignment=ft.Alignment.CENTER,
                tooltip="Clique para alterar data de pagamento",
                on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "payment_date"),
            )

        # 6. Coluna Status
        col_status = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_pago else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        size=15,
                        color=self.T["success"] if is_pago else self.T["warning"],
                    ),
                    ft.Text("Pago" if is_pago else "Pendente", size=11, weight=ft.FontWeight.W_500, color=self.T["success"] if is_pago else self.T["warning"]),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=85,
            alignment=ft.Alignment.CENTER,
            tooltip="Clique para alternar pago/pendente",
            on_click=lambda _, eid=exp_id, st=status: self._toggle_status(eid, st),
        )

        # 7. Coluna Observação
        if self.editing_cell == (exp_id, "observation"):
            input_obs = ft.TextField(
                value=obs,
                expand=True,
                height=32,
                text_size=12,
                content_padding=ft.Padding.symmetric(horizontal=6, vertical=0),
                autofocus=True,
                on_submit=lambda e, eid=exp_id: self._commit_inline_edit(eid, "observation", e.control.value),
            )
            col_obs = ft.Row(
                [
                    input_obs,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=14, icon_color=self.T["success"], on_click=lambda _, eid=exp_id: self._commit_inline_edit(eid, "observation", input_obs.value)),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14, icon_color=self.T["danger"], on_click=lambda _: self._cancel_inline_edit()),
                ],
                spacing=2,
                expand=2,
            )
        else:
            is_link = obs.startswith("http://") or obs.startswith("https://")
            obs_elements: list[ft.Control] = []
            if is_link:
                obs_elements.append(
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        icon_size=14,
                        icon_color=self.T["accent"],
                        tooltip=f"Abrir link: {obs}",
                        on_click=lambda _, u=obs: self.page_ref.launch_url(u),
                    )
                )
            obs_elements.append(
                ft.Container(
                    content=ft.Text(
                        obs if obs else "-",
                        size=11,
                        color=self.T["textMuted"] if obs else self.T["textFaint"],
                        overflow=ft.TextOverflow.ELLIPSIS,
                        no_wrap=True,
                    ),
                    expand=True,
                    tooltip=obs if obs else "Clique para adicionar observação",
                    on_click=lambda _, eid=exp_id: self._start_inline_edit(eid, "observation"),
                )
            )
            col_obs = ft.Row(obs_elements, spacing=2, expand=2, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 8. Coluna Ações
        btn_duplicate = ft.IconButton(
            icon=ft.Icons.COPY_ALL_OUTLINED,
            icon_color=self.T["accent"],
            icon_size=16,
            width=32,
            height=32,
            padding=0,
            tooltip="Duplicar despesa",
            on_click=lambda _, item=exp: self._open_expense_dialog(item, is_duplicate=True),
        )
        btn_edit = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_color=self.T["textMuted"],
            icon_size=16,
            width=32,
            height=32,
            padding=0,
            tooltip="Editar completo",
            on_click=lambda _, item=exp: self._open_expense_dialog(item),
        )
        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=self.T["danger"],
            icon_size=16,
            width=32,
            height=32,
            padding=0,
            tooltip="Excluir",
            on_click=lambda _, eid=exp_id, d=description: self._confirm_delete(eid, d),
        )
        col_actions = ft.Row([btn_duplicate, btn_edit, btn_delete], spacing=2, width=105, alignment=ft.MainAxisAlignment.END)

        return ft.Container(
            content=ft.Row(
                [
                    col_due,
                    col_cat,
                    col_desc,
                    col_amount,
                    col_payment,
                    col_status,
                    col_obs,
                    col_actions,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.only(left=12, right=14, top=4, bottom=4),
        )

    # -----------------------------------------------------------------------
    # Ações do Usuário e Tema
    # -----------------------------------------------------------------------
    def _apply_theme(self) -> None:
        """Aplica dinamicamente todos os tokens de cor do tema na interface."""
        self.T = get_tokens(self.theme_mode)
        self.bgcolor = self.T["pageBg"]
        if self.page_ref:
            self.page_ref.bgcolor = self.T["pageBg"]

        self.header_title.color = self.T["accent"]
        self.header_user.color = self.T["textMuted"]
        if isinstance(self.logo_icon, ft.Icon):
            self.logo_icon.color = self.T["accent"]

        self.month_display.color = self.T["textPrimary"]
        self.btn_prev_month.icon_color = self.T["accent"]
        self.btn_next_month.icon_color = self.T["accent"]
        self.btn_current_month.content.color = self.T["accent"]
        self.btn_current_month.style.bgcolor = self.T["surfaceSolid"]
        self.month_selector_box.bgcolor = self.T["surfaceSolid"]
        self.month_selector_box.border = ft.Border.all(1, self.T["border"])

        self.card_total.bgcolor = self.T["surfaceSolid"]
        self.card_total.border = ft.Border.all(1, self.T["border"])
        self.card_total_title.color = self.T["textMuted"]
        self.card_total_val.color = self.T["accent"]
        self.card_total_icon.color = self.T["accent"]

        self.card_pago.bgcolor = self.T["surfaceSolid"]
        self.card_pago.border = ft.Border.all(1, self.T["border"])
        self.card_pago_title.color = self.T["textMuted"]
        self.card_pago_val.color = self.T["success"]
        self.card_pago_icon.color = self.T["success"]
        if hasattr(self, "progress_ring") and self.progress_ring:
            self.progress_ring.apply_theme(self.T)

        self.card_pendente.bgcolor = self.T["surfaceSolid"]
        self.card_pendente.border = ft.Border.all(1, self.T["border"])
        self.card_pendente_title.color = self.T["textMuted"]
        self.card_pendente_val.color = self.T["warning"]
        self.card_pendente_icon.color = self.T["warning"]
        self.card_pendente_badge.color = self.T["warning"]

        self.search_field.bgcolor = self.T["surfaceSolid"]
        self.search_field.border_color = self.T["borderSubtle"]
        self.search_field.focused_border_color = self.T["accent"]
        self.search_field.color = self.T["textPrimary"]

        if hasattr(self, "filter_dropdown_container") and self.filter_dropdown_container:
            self.filter_dropdown_container.bgcolor = self.T["surfaceSolid"]
            self.filter_dropdown_container.border = ft.Border.all(1, self.T["borderSubtle"])
            self.filter_status_text.color = self.T["textPrimary"]
            self.filter_status_icon.color = self.T["textMuted"]

        for btn in (self.btn_categorias, self.btn_clonar, self.btn_backups):
            if hasattr(btn, "style") and btn.style:
                btn.style.bgcolor = self.T["surfaceSolid"]
                btn.style.side = ft.BorderSide(1, self.T["borderSubtle"])
            if hasattr(btn, "icon_color"):
                btn.icon_color = self.T["textPrimary"]
            if hasattr(btn, "content") and hasattr(btn.content, "controls"):
                btn.content.controls[0].color = self.T["textPrimary"]
                btn.content.controls[1].color = self.T["textPrimary"]

        if hasattr(self, "btn_more_options") and self.btn_more_options and hasattr(self.btn_more_options, "content"):
            self.btn_more_options.content.bgcolor = self.T["surfaceSolid"]
            self.btn_more_options.content.border = ft.Border.all(1, self.T["borderSubtle"])
            if hasattr(self.btn_more_options.content, "content") and isinstance(self.btn_more_options.content.content, ft.Icon):
                self.btn_more_options.content.content.color = self.T["textPrimary"]

        if hasattr(self, "btn_check_update") and self.btn_check_update:
            self.btn_check_update.icon_color = self.T["textMuted"]

        self.table_header.bgcolor = self.T.get("tableHeaderBg", self.T["surfaceSolid"])
        self.table_header.border = ft.Border.all(1, self.T.get("tableHeaderBorder", self.T["borderSubtle"]))
        if hasattr(self.table_header.content, "controls"):
            for c in self.table_header.content.controls:
                if hasattr(c, "content") and isinstance(c.content, ft.Text):
                    c.content.color = self.T.get("textHeader", self.T["textMuted"])

        if hasattr(self, "active_filters_banner") and self.active_filters_banner:
            self.active_filters_banner.bgcolor = self.T["warningBg"]
            self.active_filters_banner.border = ft.Border.all(1, self.T["warningBorder"])
            self.active_filter_text.color = self.T["warning"]
            self.btn_clear_all_filters.style.bgcolor = self.T["warning"]
        if hasattr(self, "btn_empty_clear_filters") and self.btn_empty_clear_filters:
            self.btn_empty_clear_filters.style.bgcolor = self.T["warning"]
        if hasattr(self, "btn_clear_search") and self.btn_clear_search:
            self.btn_clear_search.icon_color = self.T["textMuted"]

        self.divider.color = self.T["borderSubtle"]
        self.btn_theme.icon = ft.Icons.LIGHT_MODE_OUTLINED if self.theme_mode == "dark" else ft.Icons.DARK_MODE_OUTLINED
        self._update_fab()

    def _handle_toggle_theme(self, _: ft.ControlEvent) -> None:
        self.theme_mode = toggle_theme(self.page_ref)
        self._apply_theme()
        self.load_data(silent=True)

    def _change_month(self, delta: int) -> None:
        self.current_month_ref = shift_month(self.current_month_ref, delta)
        self.month_display.value = month_label(self.current_month_ref)
        # Ao navegar entre meses, reseta a busca de texto para não travar a exibição
        if self.search_query:
            self.search_query = ""
            self.search_field.value = ""
            if hasattr(self, "btn_clear_search"):
                self.btn_clear_search.visible = False
        self._update_active_filters_banner()
        self.load_data()

    def _reset_to_current_month(self) -> None:
        self.current_month_ref = get_current_month_ref()
        self.month_display.value = month_label(self.current_month_ref)
        # Ao voltar para o mês atual, garante restauração completa da visão normal
        self.search_query = ""
        self.search_field.value = ""
        if hasattr(self, "btn_clear_search"):
            self.btn_clear_search.visible = False
        self.status_filter = "todos"
        self.filter_dropdown.value = "todos"
        self._update_filter_status_label()
        self._update_active_filters_banner()
        self.load_data()

    def _clear_search(self) -> None:
        """Limpa a busca textual e re-renderiza a lista."""
        self.search_query = ""
        self.search_field.value = ""
        if hasattr(self, "btn_clear_search"):
            self.btn_clear_search.visible = False
        self._update_active_filters_banner()
        self._render_expenses_list()
        if self.page_ref:
            self.page_ref.update()

    def _clear_all_filters(self) -> None:
        """Restaura a visão normal limpando todos os filtros aplicados (busca e status)."""
        self.search_query = ""
        self.search_field.value = ""
        if hasattr(self, "btn_clear_search"):
            self.btn_clear_search.visible = False
        self.status_filter = "todos"
        self.filter_dropdown.value = "todos"
        self._update_filter_status_label()
        self._update_active_filters_banner()
        self._render_expenses_list()
        if self.page_ref:
            self.page_ref.update()

    def _update_active_filters_banner(self) -> None:
        """Sincroniza o banner informativo de filtros ativos e o botão de limpar busca."""
        if not hasattr(self, "active_filters_banner"):
            return
        has_search = bool(self.search_query.strip())
        has_status = self.status_filter != "todos"
        if hasattr(self, "btn_clear_search"):
            self.btn_clear_search.visible = has_search
        if has_search or has_status:
            parts = []
            if has_status:
                st_name = "Pendentes" if self.status_filter == "pendente" else "Pagos"
                parts.append(f"Status: {st_name}")
            if has_search:
                parts.append(f"Busca: '{self.search_query}'")
            self.active_filter_text.value = "Filtrando por: " + " • ".join(parts)
            self.active_filters_banner.visible = True
        else:
            self.active_filters_banner.visible = False

    def _on_search_change(self, e: ft.ControlEvent) -> None:
        self.search_query = e.control.value or ""
        self._update_active_filters_banner()
        self._render_expenses_list()
        self.page_ref.update()

    def _on_status_filter_selected(self, key: str) -> None:
        self.status_filter = key
        self.filter_dropdown.value = key
        self._update_filter_status_label()
        self._update_active_filters_banner()
        self._render_expenses_list()
        self.page_ref.update()

    def _on_filter_change(self, e: Any) -> None:
        val = getattr(e.control, "value", "todos") if hasattr(e, "control") else str(e)
        self._on_status_filter_selected(val)

    def _toggle_status(self, expense_id: str, current_status: str) -> None:
        try:
            toggle_expense_status(expense_id, current_status)
            self.load_data(silent=True)
        except Exception as exc:
            self._show_snack(f"Erro ao alternar status: {exc}", is_error=True)

    # -----------------------------------------------------------------------
    # Modal de Pendências do Mês Anterior
    # -----------------------------------------------------------------------
    def _open_prev_month_alert_modal(self) -> None:
        prev_ref = self.prev_month_pending.get("prev_month_ref", "")
        items = self.prev_month_pending.get("items", [])
        count = self.prev_month_pending.get("count", 0)
        total = self.prev_month_pending.get("total_amount", 0.0)

        if count == 0:
            content_col = ft.Column(
                [
                    ft.Text(f"Parabéns! Não existem despesas pendentes em {month_label(prev_ref)}.", size=13, color=self.T["textPrimary"]),
                ],
                tight=True,
                spacing=8,
            )
        else:
            items_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=220)
            for exp in items:
                desc = exp.get("description", "")
                amt = float(exp.get("amount") or 0.0)
                due = exp.get("due_date", "")
                due_d = due.split("-")[-1] if "-" in due else due

                cat_info = exp.get("category") or {}
                cat_name = cat_info.get("name") if isinstance(cat_info, dict) else "Outros"
                cat_color = (cat_info.get("color") or cat_info.get("color_hex") if isinstance(cat_info, dict) else None) or "#94A3B8"

                cat_bg, cat_fg, cat_border = get_badge_colors(cat_color, is_light=self.theme_mode == "light")
                cat_badge = ft.Container(
                    content=ft.Text(cat_name, size=10, weight=ft.FontWeight.W_600, color=cat_fg),
                    bgcolor=cat_bg,
                    border=ft.Border.all(1, cat_border) if cat_border else None,
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                )
                due_badge = ft.Container(
                    content=ft.Text(f"Dia {due_d}", size=10, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                    bgcolor=self.T["pageBg"],
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                )

                top_pending_row = ft.Row(
                    [
                        ft.Row([cat_badge, due_badge], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(format_brl(amt), size=12, weight=ft.FontWeight.BOLD, color=self.T["warning"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )

                bottom_pending_row = ft.Row(
                    [
                        ft.Text(
                            desc,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=self.T["textPrimary"],
                            expand=True,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            [
                                ft.Text("Ir", size=10, weight=ft.FontWeight.BOLD, color=self.T["accent"]),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=self.T["accent"]),
                            ],
                            spacing=3,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )

                row_item = ft.Container(
                    content=ft.Column(
                        [top_pending_row, bottom_pending_row],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=self.T["surfaceSolid"],
                    border=ft.Border.all(1, self.T["borderSubtle"]),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ink=True,
                    tooltip=f"Clique para navegar para '{desc}' em {month_label(prev_ref)}",
                    on_click=lambda _, d=desc: navigate_to_expense(d),
                )
                items_list.controls.append(row_item)

            content_col = ft.Column(
                [
                    ft.Text(
                        f"{count} pendência{'s' if count != 1 else ''} • Total em aberto: {format_brl(total)}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=self.T["warning"],
                    ),
                    items_list,
                ],
                spacing=10,
                tight=True,
            )

        def navigate_to_expense(target_desc: str = "") -> None:
            self._close_dialog(dlg)
            self.current_month_ref = prev_ref
            self.month_display.value = month_label(prev_ref)
            self.status_filter = "pendente"
            self.filter_dropdown.value = "pendente"
            self._update_filter_status_label()
            if target_desc:
                self.search_query = target_desc
                self.search_field.value = target_desc
                if hasattr(self, "btn_clear_search"):
                    self.btn_clear_search.visible = True
            else:
                self.search_query = ""
                self.search_field.value = ""
                if hasattr(self, "btn_clear_search"):
                    self.btn_clear_search.visible = False
            self._update_active_filters_banner()
            self.load_data()
            if target_desc:
                self._show_snack(f"Navegou para {month_label(prev_ref)}: {target_desc}")
            else:
                self._show_snack(f"Navegou para pendências de {month_label(prev_ref)}")

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0

        dlg_w = min(page_w - 32, 520)

        dlg_header = build_modal_header(
            title=f"Pendências de {month_label(prev_ref)}",
            on_close=lambda: self._close_dialog(dlg),
            theme_tokens=self.T,
        )

        dlg = ft.AlertDialog(
            title=dlg_header,
            content=ft.Container(content=content_col, width=dlg_w),
            bgcolor=self.T["surface"],
            actions=[
                ft.Button(
                    content=ft.Text("Fechar", color=self.T["textMuted"]),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["surfaceSolid"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._close_dialog(dlg),
                ),
                ft.Button(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CALENDAR_MONTH, size=15, color="#08090F"),
                            ft.Text(f"Ver todas em {month_label(prev_ref)}", color="#08090F", weight=ft.FontWeight.BOLD, size=12),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["warning"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: navigate_to_expense(""),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dlg)

    # -----------------------------------------------------------------------
    # Confirmação de Exclusão
    # -----------------------------------------------------------------------
    def _confirm_delete(self, expense_id: str, description: str) -> None:
        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0

        dlg_w = min(page_w - 32, 400)

        del_header = build_modal_header(
            title="Confirmar Exclusão",
            on_close=lambda: self._close_dialog(dlg),
            theme_tokens=self.T,
        )

        dlg = ft.AlertDialog(
            title=del_header,
            content=ft.Container(
                content=ft.Text(f"Deseja realmente excluir a despesa '{description}'?", size=13, color=self.T["textPrimary"]),
                width=dlg_w,
            ),
            bgcolor=self.T["surface"],
            actions=[
                ft.Button(
                    content=ft.Text("Cancelar", color=self.T["textMuted"]),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["surfaceSolid"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._close_dialog(dlg),
                ),
                ft.Button(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.DELETE_OUTLINE, size=16, color="#FFFFFF"),
                            ft.Text("Excluir", weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["danger"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._execute_delete(dlg, expense_id),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dlg)

    def _execute_delete(self, dlg: ft.AlertDialog, expense_id: str) -> None:
        self._close_dialog(dlg)
        try:
            delete_expense(expense_id)
            self.load_data(silent=True)
            self._show_snack("Despesa excluída com sucesso!")
        except Exception as exc:
            self._show_snack(f"Erro ao excluir despesa: {exc}", is_error=True)

    # -----------------------------------------------------------------------
    # Modal de Criação / Edição Completa de Despesa (Flet 1.0)
    # -----------------------------------------------------------------------
    def _open_expense_dialog(self, expense: dict[str, Any] | None = None, is_duplicate: bool = False) -> None:
        is_edit = expense is not None and not is_duplicate
        if is_duplicate:
            title = "Duplicar Despesa"
        elif is_edit:
            title = "Editar Despesa"
        else:
            title = "Nova Despesa"

        desc_init = ""
        if expense:
            desc_init = f"{expense.get('description', '')} (Cópia)" if is_duplicate else expense.get("description", "")

        # Header do Modal com Logo MAI Finance + Título + Fechar X via build_modal_header
        modal_header = build_modal_header(
            title=title,
            on_close=lambda: self._close_dialog(dlg),
            theme_tokens=self.T,
        )

        desc_field = ft.TextField(
            label="Descrição *",
            hint_text="Ex: Supermercado, Aluguel...",
            value=desc_init,
            dense=True,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
        )

        amount_field = ft.TextField(
            label="Valor (R$) *",
            hint_text="0,00",
            value=str(expense.get("amount", "")) if expense else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            expand=1,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
        )

        default_due = expense.get("due_date", "") if expense else f"{self.current_month_ref}-10"
        due_date_field = ft.TextField(
            label="Vencimento *",
            hint_text="AAAA-MM-DD",
            value=default_due,
            dense=True,
            expand=1,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
        )

        cat_options = [ft.dropdown.Option(key="", text="Sem Categoria")] + [
            ft.dropdown.Option(key=str(c.get("id")), text=c.get("name", ""))
            for c in self.available_categories
            if c.get("id")
        ]
        curr_cat_id = str(expense.get("category_id") or "") if expense and expense.get("category_id") else ""
        category_dropdown = ft.Dropdown(
            label="Categoria",
            options=cat_options,
            value=curr_cat_id,
            dense=True,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
        )

        # Seletor Segmentado de Status com Botões Interativos
        status_init = "pendente" if is_duplicate else (expense.get("status", "pendente") if expense else "pendente")
        selected_status = {"value": status_init}

        btn_pendente = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SCHEDULE, size=15, color=self.T["warning"]),
                    ft.Text("Pendente", size=12, weight=ft.FontWeight.W_600, color=self.T["warning"]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor=self.T["warningBg"] if selected_status["value"] == "pendente" else None,
            border=ft.Border.all(1.5, self.T["warning"]) if selected_status["value"] == "pendente" else ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=10),
            expand=True,
            ink=True,
        )

        btn_pago = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=15, color=self.T["success"]),
                    ft.Text("Pago", size=12, weight=ft.FontWeight.W_600, color=self.T["success"]),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor=self.T["successBg"] if selected_status["value"] == "pago" else None,
            border=ft.Border.all(1.5, self.T["success"]) if selected_status["value"] == "pago" else ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=10),
            expand=True,
            ink=True,
        )

        def set_status_val(new_st: str) -> None:
            selected_status["value"] = new_st
            is_p = new_st == "pago"
            btn_pendente.bgcolor = self.T["warningBg"] if not is_p else None
            btn_pendente.border = ft.Border.all(1.5, self.T["warning"]) if not is_p else ft.Border.all(1, self.T["borderSubtle"])
            btn_pago.bgcolor = self.T["successBg"] if is_p else None
            btn_pago.border = ft.Border.all(1.5, self.T["success"]) if is_p else ft.Border.all(1, self.T["borderSubtle"])
            self.page_ref.update()

        btn_pendente.on_click = lambda _: set_status_val("pendente")
        btn_pago.on_click = lambda _: set_status_val("pago")

        status_selector = ft.Column(
            [
                ft.Text("Status do Pagamento", size=11, weight=ft.FontWeight.W_500, color=self.T["textMuted"]),
                ft.Row([btn_pendente, btn_pago], spacing=8),
            ],
            spacing=4,
        )

        obs_field = ft.TextField(
            label="Observação (opcional)",
            hint_text="Anotações adicionais",
            value=expense.get("observation", "") if expense else "",
            dense=True,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
        )

        form_error = ft.Text("", color=self.T["danger"], size=12, visible=False)

        # Botões de Ação
        btn_cancel = ft.Button(
            content=ft.Text("Cancelar", color=self.T["textMuted"]),
            style=ft.ButtonStyle(
                bgcolor=self.T["surfaceSolid"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._close_dialog(dlg),
        )

        btn_save = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                    ft.Text("Salvar", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=6,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        is_saving = {"active": False}

        def save_action(_: ft.ControlEvent) -> None:
            if is_saving["active"]:
                return

            desc = (desc_field.value or "").strip()
            if not desc:
                form_error.value = "A descrição é obrigatória."
                form_error.visible = True
                self.page_ref.update()
                return

            try:
                val = float((amount_field.value or "0").replace(",", "."))
                if val < 0:
                    raise ValueError
            except Exception:
                form_error.value = "Informe um valor numérico válido."
                form_error.visible = True
                self.page_ref.update()
                return

            due = (due_date_field.value or "").strip()
            if not due or len(due) < 10:
                form_error.value = "Informe o vencimento no formato AAAA-MM-DD."
                form_error.visible = True
                self.page_ref.update()
                return

            # Proteção contra duplo clique e feedback imediato no botão
            is_saving["active"] = True
            btn_save.disabled = True
            btn_save.content = MaiLoading.button_spinner("Salvando...")
            form_error.visible = False
            self.page_ref.update()

            payload = {
                "description": desc,
                "amount": val,
                "due_date": due,
                "category_id": category_dropdown.value if category_dropdown.value else None,
                "status": selected_status["value"],
                "observation": (obs_field.value or "").strip() or None,
                "month_ref": f"{due[:7]}-01",
            }

            try:
                if is_edit and expense:
                    update_expense(expense["id"], payload)
                    success_msg = "Despesa atualizada com sucesso!"
                else:
                    create_expense(payload)
                    success_msg = "Despesa duplicada com sucesso!" if is_duplicate else "Despesa criada com sucesso!"

                # 1. FECHA O MODAL IMEDIATAMENTE (DETERMINÍSTICO)
                self._close_dialog(dlg)

                # 2. RECARREGA OS DADOS PARA EXIBIR A DESPESA NA TABELA
                self.load_data(silent=True)

                # 3. EXIBE A NOTIFICAÇÃO DE SUCESSO
                self._show_snack(success_msg)

            except Exception as exc:
                is_saving["active"] = False
                btn_save.disabled = False
                btn_save.content = ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                        ft.Text("Salvar", weight=ft.FontWeight.BOLD, color="#08090F"),
                    ],
                    spacing=6,
                    tight=True,
                )
                form_error.value = f"Erro ao salvar: {exc}"
                form_error.visible = True
                self.page_ref.update()

        btn_save.on_click = save_action

        page_w = self._get_current_width()
        dlg_w = min(page_w - 32, 430)

        # Campos Valor e Vencimento em linha compacta
        row_amount_due = ft.Row(
            [amount_field, due_date_field],
            spacing=10,
        )

        dlg = ft.AlertDialog(
            title=modal_header,
            bgcolor=self.T["surface"],
            content=ft.Container(
                content=ft.Column(
                    [
                        desc_field,
                        row_amount_due,
                        category_dropdown,
                        status_selector,
                        obs_field,
                        form_error,
                    ],
                    spacing=10,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=dlg_w,
            ),
            actions=[
                btn_cancel,
                btn_save,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dlg)

    # -----------------------------------------------------------------------
    # Utilitários de Diálogo e Feedback (Flet 1.0)
    # -----------------------------------------------------------------------
    def _open_dialog(self, dlg: ft.AlertDialog) -> None:
        if hasattr(self.page_ref, "show_dialog"):
            self.page_ref.show_dialog(dlg)
        else:
            self.page_ref.dialog = dlg
            dlg.open = True
            self.page_ref.update()

    def _close_dialog(self, dlg: ft.AlertDialog | None = None) -> None:
        if dlg is not None:
            dlg.open = False
        if hasattr(self.page_ref, "pop_dialog"):
            try:
                self.page_ref.pop_dialog()
            except Exception:
                pass
        if hasattr(self.page_ref, "dialog") and self.page_ref.dialog == dlg:
            self.page_ref.dialog = None
        self.page_ref.update()

    def _show_snack(self, message: str, is_error: bool = False) -> None:
        snack = ft.SnackBar(
            content=ft.Text(message, color="#FFFFFF", weight=ft.FontWeight.W_500),
            bgcolor=self.T["danger"] if is_error else self.T["successBg"],
            action="OK",
        )
        self.page_ref.snack_bar = snack
        snack.open = True
        self.page_ref.update()

    def _check_update_silently(self) -> None:
        """Verifica em segundo plano se há atualização sem incomodar o usuário caso esteja atualizado."""
        try:
            update = check_for_updates()
            if update and self.page_ref:
                open_update_dialog(self.page_ref, update)
        except Exception as exc:
            print(f"[Dashboard] Checagem silenciosa de atualização: {exc}")

    def _manual_check_update(self) -> None:
        """Verificação sob demanda disparada pelo usuário via botão ou menu."""
        self._show_snack("Verificando atualizações no GitHub...")

        def _worker():
            try:
                update = check_for_updates()
                if update and self.page_ref:
                    open_update_dialog(self.page_ref, update)
                else:
                    self._show_snack(f"O MAI Finance já está na versão mais recente (v{CURRENT_VERSION}).")
            except Exception as exc:
                self._show_snack(f"Não foi possível verificar atualizações: {exc}", is_error=True)

        threading.Thread(target=_worker, daemon=True).start()
