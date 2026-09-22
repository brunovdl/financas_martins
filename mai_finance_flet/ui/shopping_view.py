"""
shopping_view.py — Tela da Lista de Compras Inteligente do MAI Finance (T-019 / Design System).

Implementa:
- Barra de chips para adicionar sugestões frequentes com 1 toque (AC-022)
- Modal dedicado para inclusão de itens acionado pelo FloatingActionButton '+'
- Seletor de Cidade/UF e Mercado no banner com persistência no client storage
- Cotação direcionada por IA com Groq para mercado específico ou comparativo regional (AC-024, AC-025)
- Suporte dinâmico e robusto à alternância de tema Dark/Light com contraste perfeito
- Sincronização em tempo real entre Bruno e sua esposa (AC-027)
- Inicialização do Modo Mercado (AC-026)
"""
from __future__ import annotations

import threading
from typing import Any, Callable
import flet as ft

from services.shopping_service import (
    add_shopping_item,
    get_all_items,
    get_items_grouped_by_corridor,
    get_quick_suggestions,
)
from db.shopping import delete_shopping_item, update_shopping_item
from services.market_ai_service import quote_shopping_list
from services.geo_service import set_custom_location, set_configured_market, get_device_location, detect_device_location_auto
from services.shopping_realtime import ShoppingRealtimeSync
from ui.components.shopping_item_card import build_shopping_item_card
from ui.components.shopping_add_item_modal import open_shopping_add_item_modal
from ui.components.shopping_location_modal import open_shopping_location_modal
from ui.components.shopping_quote_summary_modal import open_shopping_quote_summary_modal
from ui.components.market_quote_modal import open_market_quote_modal
from ui.components.mai_loading import MaiLoading
from ui.nav import toggle_theme, get_current_theme
from ui.theme import get_tokens, format_brl
from ui.storage_util import get_local_item, set_local_item
from ui.components.camera_price_scanner_modal import open_camera_price_scanner


class ShoppingView(ft.Container):
    """View completa para gestão da Lista de Compras Inteligente."""

    def __init__(
        self,
        page: ft.Page,
        on_back_to_dashboard: Callable[[], None],
        on_open_market_mode: Callable[[str | None], None],
    ) -> None:
        super().__init__()
        self.page_ref = page
        self.on_back_to_dashboard = on_back_to_dashboard
        self.on_open_market_mode = on_open_market_mode

        self.expand = True
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)
        self.bgcolor = self.T["pageBg"]
        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8)

        self.items: list[dict[str, Any]] = []

        # Localização e mercado recuperados do client storage
        saved_city = get_local_item(page, "shopping_city")
        self.city: str = saved_city if saved_city else get_device_location().get("city", "São Paulo, SP")

        saved_market = get_local_item(page, "shopping_market")
        self.selected_market: str | None = saved_market if (saved_market and saved_market.strip()) else None

        # Sincroniza estado inicial com o serviço de geo
        set_custom_location(city=self.city)
        set_configured_market(self.selected_market)

        self.is_loading = False

        # Inicia escuta Realtime
        self.realtime_sync = ShoppingRealtimeSync(
            on_change_callback=self._handle_realtime_update,
            interval_seconds=3.0,
        )

        self._build_ui()

    def did_mount(self) -> None:
        """Inicializa carregamento de dados, conexão em tempo real, FAB e detecção de cidade."""
        self._setup_fab()
        self.load_data()
        self.realtime_sync.start()
        self._trigger_auto_location()

    def _trigger_auto_location(self) -> None:
        """Detecta automaticamente a cidade/UF do usuário: GPS nativo (DEC-029) + fallback GeoIP."""
        saved_city = get_local_item(self.page_ref, "shopping_city")
        if saved_city and saved_city.strip():
            return

        # Tenta GPS nativo primeiro (async)
        async def _try_gps():
            from services.geo_service import detect_location_gps
            gps_result = await detect_location_gps(self.page_ref)
            if gps_result:
                detected_city = gps_result.get("city")
                if detected_city and detected_city != self.city:
                    self.city = detected_city
                    set_custom_location(city=self.city)
                    self.market_city_label.value = self.city
                    try:
                        self.market_city_label.update()
                    except Exception:
                        if self.page_ref:
                            self.page_ref.update()
                return

            # Fallback: GeoIP em background thread
            def _worker():
                loc = detect_device_location_auto()
                detected_city = loc.get("city")
                if detected_city and detected_city != self.city:
                    self.city = detected_city
                    set_custom_location(city=self.city)
                    def _update_ui():
                        self.market_city_label.value = self.city
                        try:
                            self.market_city_label.update()
                        except Exception:
                            if self.page_ref:
                                self.page_ref.update()
                    if hasattr(self.page_ref, "run_thread"):
                        self.page_ref.run_thread(_update_ui)
                    else:
                        _update_ui()

            threading.Thread(target=_worker, daemon=True).start()

        if hasattr(self.page_ref, "run_task"):
            self.page_ref.run_task(_try_gps)
        else:
            # Fallback direto para GeoIP se run_task não está disponível
            def _worker():
                loc = detect_device_location_auto()
                detected_city = loc.get("city")
                if detected_city and detected_city != self.city:
                    self.city = detected_city
                    set_custom_location(city=self.city)
                    def _update_ui():
                        self.market_city_label.value = self.city
                        try:
                            self.market_city_label.update()
                        except Exception:
                            if self.page_ref:
                                self.page_ref.update()
                    if hasattr(self.page_ref, "run_thread"):
                        self.page_ref.run_thread(_update_ui)
                    else:
                        _update_ui()
            threading.Thread(target=_worker, daemon=True).start()

    def will_unmount(self) -> None:
        """Encerra listener de realtime e limpa o FAB ao sair da tela."""
        self.realtime_sync.stop()
        if hasattr(self.page_ref, "floating_action_button"):
            self.page_ref.floating_action_button = None

    def _setup_fab(self) -> None:
        """Configura o botão '+' flutuante para adicionar itens à lista de compras."""
        if hasattr(self.page_ref, "floating_action_button"):
            self.page_ref.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=self.T["accent"],
                tooltip="Adicionar Item à Lista",
                on_click=lambda _: self._open_add_item_modal(),
            )
            try:
                self.page_ref.update()
            except Exception:
                pass

    def _open_add_item_modal(self) -> None:
        """Abre o diálogo padronizado para adicionar novo item à lista."""
        open_shopping_add_item_modal(
            page=self.page_ref,
            on_item_added=self._on_item_added,
            current_market=self.selected_market,
        )

    def _on_item_added(self, name: str) -> None:
        """Callback após inclusão bem-sucedida de um item."""
        self.load_data()
        self._show_snack(f"'{name}' adicionado à lista!")

    def _handle_realtime_update(self, new_items: list[dict[str, Any]]) -> None:
        """Callback acionado quando o outro celular altera a lista."""
        self.items = new_items
        self._refresh_list_content()
        try:
            self.page_ref.update()
        except Exception:
            pass

    def load_data(self) -> None:
        """Carrega itens do banco de dados e recalcula métricas."""
        self.items = get_all_items()
        self.realtime_sync.trigger_local_update(self.items)
        self._refresh_list_content()
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _build_ui(self) -> None:
        # Header da Lista de Compras
        self.btn_back = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=self.T["textPrimary"],
            tooltip="Voltar ao Painel",
            on_click=lambda _: self._handle_back(),
        )

        self.title_icon = ft.Icon(ft.Icons.SHOPPING_CART, size=20, color=self.T["accent"])
        self.title_text = ft.Text("Lista de Compras", size=18, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"])
        self.subtitle_text = ft.Text("Compartilhada em tempo real com a casa", size=11, color=self.T["textMuted"])

        title_col = ft.Column(
            [
                ft.Row([self.title_icon, self.title_text], spacing=6),
                self.subtitle_text,
            ],
            spacing=1,
        )

        self.btn_theme = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE_OUTLINED if self.theme_mode == "dark" else ft.Icons.DARK_MODE_OUTLINED,
            icon_color=self.T["accent"],
            tooltip="Alternar Tema",
            on_click=self._toggle_theme_view,
        )

        header_row = ft.Row(
            [
                ft.Row([self.btn_back, title_col], spacing=4),
                self.btn_theme,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Chips de sugestões frequentes (AC-022)
        self.lbl_shortcuts = ft.Text("Atalhos Frequentes:", size=11, weight=ft.FontWeight.BOLD, color=self.T["textMuted"])
        self.chips_row = ft.Row(wrap=True, spacing=6)
        self._load_quick_chips()

        # Banner de Localização & Mercado Ativo com IA
        self.market_icon = ft.Icon(ft.Icons.LOCATION_ON, size=18, color=self.T["accent"])
        self.market_city_label = ft.Text(
            f"📍 {self.city}",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=self.T["textPrimary"],
        )
        self.market_name_label = ft.Text(
            f"🛒 {self.selected_market if self.selected_market else 'Todos os mercados da cidade'}",
            size=11,
            color=self.T["textMuted"],
            weight=ft.FontWeight.W_500,
        )

        loc_text_col = ft.Column(
            [self.market_city_label, self.market_name_label],
            spacing=1,
            expand=True,
        )

        self.btn_edit_loc = ft.IconButton(
            icon=ft.Icons.EDIT_LOCATION_ALT_OUTLINED,
            icon_color=self.T["accent"],
            icon_size=18,
            tooltip="Alterar Cidade e Mercado",
            on_click=lambda _: self._open_location_modal(),
        )

        self.btn_quote_ai = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=15, color="#08090F"),
                    ft.Text("Cotar com IA", size=11, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ),
            height=34,
            on_click=lambda _: self._handle_quote_ai(),
        )

        banner_bg = self.T["surfaceSolid"] if self.theme_mode == "dark" else "#FFFFFF"
        self.market_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Row([self.market_icon, loc_text_col, self.btn_edit_loc], spacing=6, expand=True),
                    self.btn_quote_ai,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=banner_bg,
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            on_click=lambda _: self._open_location_modal(),
        )

        # Botão principal Modo Mercado
        self.btn_market_mode = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=20, color="#08090F"),
                    ft.Text("INICIAR MODO MERCADO", size=13, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["success"],
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            ),
            height=46,
            on_click=lambda _: self.on_open_market_mode(self.selected_market),
        )

        # Lista de Itens por Corredor
        self.items_list_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        self.content = ft.Column(
            [
                header_row,
                self.lbl_shortcuts,
                self.chips_row,
                self.market_banner,
                self.btn_market_mode,
                self.items_list_col,
            ],
            spacing=10,
            expand=True,
        )

    def _handle_back(self) -> None:
        """Volta ao painel principal garantindo limpeza de FAB."""
        if hasattr(self.page_ref, "floating_action_button"):
            self.page_ref.floating_action_button = None
        self.on_back_to_dashboard()

    def _open_location_modal(self) -> None:
        """Abre modal para configurar cidade e mercado."""
        open_shopping_location_modal(
            page=self.page_ref,
            current_city=self.city,
            current_market=self.selected_market,
            on_location_saved=self._on_location_saved,
        )

    def _on_location_saved(self, new_city: str, new_market: str | None) -> None:
        """Aplica a nova localização e mercado selecionados."""
        self.city = new_city
        self.selected_market = new_market
        set_custom_location(city=self.city)
        set_configured_market(self.selected_market)

        self.market_city_label.value = f"📍 {self.city}"
        self.market_name_label.value = f"🛒 {self.selected_market if self.selected_market else 'Todos os mercados da cidade'}"
        self.page_ref.update()
        self._show_snack("Localização e mercado atualizados!")

    def _load_quick_chips(self) -> None:
        """Carrega chips clicáveis para inclusão rápida com 1 toque (AC-022)."""
        suggestions = get_quick_suggestions()[:8]
        chips: list[ft.Control] = []
        chip_bg = self.T["surfaceSolid"] if self.theme_mode == "dark" else "#FFFFFF"

        for s in suggestions:
            name = s["name"]
            unit = s.get("unit", "un")
            corridor = s.get("corridor", "Outros")

            btn_chip = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=12, color=self.T["accent"]),
                        ft.Text(name, size=11, color=self.T["textPrimary"], weight=ft.FontWeight.W_500),
                    ],
                    spacing=3,
                    tight=True,
                ),
                bgcolor=chip_bg,
                border=ft.Border.all(1, self.T["borderSubtle"]),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                on_click=lambda _, n=name, u=unit, c=corridor: self._add_quick_item(n, u, c),
            )
            chips.append(btn_chip)
        self.chips_row.controls = chips

    def _add_quick_item(self, name: str, unit: str, corridor: str) -> None:
        """Adiciona item imediatamente pelo chip de atalho."""
        add_shopping_item(
            name=name,
            quantity=1.0,
            unit=unit,
            corridor=corridor,
            market_name=self.selected_market,
        )
        self.load_data()
        self._show_snack(f"'{name}' adicionado à lista!")

    def _handle_quote_ai(self) -> None:
        """Dispara a cotação de preços com IA para a cidade e mercado configurados."""
        if not self.items:
            self._show_snack("Cadastre itens antes de cotar nos mercados!")
            return

        # Ativa feedback de carregamento
        self.btn_quote_ai.disabled = True
        self.btn_quote_ai.content = MaiLoading.button_spinner("Cotando IA...")
        self.page_ref.update()

        target_market = self.selected_market
        city = self.city

        def run_quote():
            quote_data = quote_shopping_list(
                items=self.items,
                city=city,
                target_market=target_market,
            )

            def apply_prices_and_refresh(market_name: str, quoted_items: list[dict[str, Any]]):
                self.selected_market = market_name
                set_configured_market(market_name)
                try:
                    set_local_item(self.page_ref, "shopping_market", market_name)
                except Exception:
                    pass
                self.market_name_label.value = f"🛒 {market_name}"

                for q_it in quoted_items:
                    it_id = q_it.get("id")
                    if it_id:
                        update_shopping_item(it_id, {
                            "estimated_price": q_it.get("unit_price", 0.0),
                            "market_name": market_name,
                        })
                self.load_data()
                self._show_snack(f"Preços de '{market_name}' aplicados à lista!")

            def finish_ui():
                self.btn_quote_ai.disabled = False
                self.btn_quote_ai.content = ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=15, color="#08090F"),
                        ft.Text("Cotar com IA", size=11, weight=ft.FontWeight.BOLD, color="#08090F"),
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                )
                self.page_ref.update()

                is_single = quote_data.get("single_market", False)
                if is_single and target_market:
                    open_shopping_quote_summary_modal(
                        page=self.page_ref,
                        market_name=target_market,
                        city=city,
                        quote_data=quote_data,
                        on_apply_prices=apply_prices_and_refresh,
                    )
                else:
                    open_market_quote_modal(
                        page=self.page_ref,
                        quote_data=quote_data,
                        on_market_selected=apply_prices_and_refresh,
                    )

            self.page_ref.run_thread(finish_ui)

        threading.Thread(target=run_quote, daemon=True).start()

    def _handle_toggle_bought(self, item_id: str, is_bought: bool) -> None:
        """Alterna o status de comprado do item e sincroniza com o banco e realtime."""
        update_shopping_item(item_id, {"is_bought": is_bought})
        self.load_data()

    def _handle_delete_item(self, item_id: str) -> None:
        """Exclui item da lista de compras."""
        delete_shopping_item(item_id)
        self.load_data()

    def _handle_edit_item(self, item: dict[str, Any]) -> None:
        """Abre o diálogo de edição do item selecionado."""
        open_shopping_add_item_modal(
            page=self.page_ref,
            on_item_added=lambda _: self.load_data(),
            current_market=self.selected_market,
            item_to_edit=item,
        )

    def _handle_scan_price(self, item: dict[str, Any]) -> None:
        """Abre o scanner de câmera zero-toque para ler a etiqueta de gôndola (DEC-026)."""
        def _on_price_detected(item_id: str, price: float) -> None:
            update_shopping_item(item_id, {
                "actual_price": price,
                "estimated_price": price,
            })
            self.load_data()
            self._show_snack(f"✅ Preço de {format_brl(price)} aplicado a '{item.get('name', 'Item')}'!")

        open_camera_price_scanner(
            page=self.page_ref,
            item=item,
            theme_mode=self.theme_mode,
            on_price_detected=_on_price_detected,
        )

    def _refresh_list_content(self) -> None:
        """Re-renderiza a listagem agrupada por corredores."""
        grouped = get_items_grouped_by_corridor(self.items)
        controls: list[ft.Control] = []

        if not grouped:
            empty_box = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=40, color=self.T["textMuted"]),
                        ft.Text("Sua lista de compras está vazia!", size=14, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"]),
                        ft.Text("Clique nos atalhos ou no botão '+' para adicionar.", size=12, color=self.T["textMuted"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(vertical=24),
            )
            controls.append(empty_box)
        else:
            for corridor_name, corridor_items in grouped.items():
                header = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.LOCAL_GROCERY_STORE_OUTLINED, size=14, color=self.T["accent"]),
                            ft.Text(corridor_name.upper(), size=11, weight=ft.FontWeight.BOLD, color=self.T["accent"]),
                            ft.Text(f"({len(corridor_items)})", size=11, color=self.T["textMuted"]),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.only(top=6, bottom=2),
                )
                controls.append(header)

                for item in corridor_items:
                    card = build_shopping_item_card(
                        item=item,
                        theme_mode=self.theme_mode,
                        on_delete=self._handle_delete_item,
                        on_toggle=self._handle_toggle_bought,
                        on_edit=self._handle_edit_item,
                        on_scan_price=self._handle_scan_price,
                    )
                    controls.append(card)

        self.items_list_col.controls = controls

    def _apply_theme(self) -> None:
        """Aplica dinamicamente todos os tokens de cor do tema na interface."""
        self.T = get_tokens(self.theme_mode)
        self.bgcolor = self.T["pageBg"]
        if self.page_ref:
            self.page_ref.bgcolor = self.T["pageBg"]

        # Cabeçalho
        self.btn_back.icon_color = self.T["textPrimary"]
        self.title_icon.color = self.T["accent"]
        self.title_text.color = self.T["textPrimary"]
        self.subtitle_text.color = self.T["textMuted"]
        self.btn_theme.icon = ft.Icons.LIGHT_MODE_OUTLINED if self.theme_mode == "dark" else ft.Icons.DARK_MODE_OUTLINED
        self.btn_theme.icon_color = self.T["accent"]

        # Atalhos
        self.lbl_shortcuts.color = self.T["textMuted"]
        self._load_quick_chips()

        # Banner de Localização
        banner_bg = self.T["surfaceSolid"] if self.theme_mode == "dark" else "#FFFFFF"
        self.market_banner.bgcolor = banner_bg
        self.market_banner.border = ft.Border.all(1, self.T["borderSubtle"])
        self.market_icon.color = self.T["accent"]
        self.market_city_label.color = self.T["textPrimary"]
        self.market_name_label.color = self.T["textMuted"]
        self.btn_edit_loc.icon_color = self.T["accent"]

        # Botão Modo Mercado
        self.btn_market_mode.style.bgcolor = self.T["success"]

        # FAB e listagem
        self._setup_fab()
        self._refresh_list_content()

    def _toggle_theme_view(self, _: Any) -> None:
        """Alterna tema escuro/claro e reaplica tokens completos."""
        self.theme_mode = toggle_theme(self.page_ref)
        self._apply_theme()
        self.page_ref.update()

    def _show_snack(self, message: str) -> None:
        """Exibe notificação toast na tela."""
        snack = ft.SnackBar(
            content=ft.Text(message, color="#08090F", weight=ft.FontWeight.BOLD),
            bgcolor=self.T["accent"],
            duration=3000,
        )
        self.page_ref.snack_bar = snack
        snack.open = True
        self.page_ref.update()
