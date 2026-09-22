"""
shopping_market_mode.py — Interface dedicada para compras presenciais no supermercado (T-020).

Implementa:
- Alvos de toque grandes (≥ 48px) para marcação com uma mão (AC-026)
- Métricas em tempo real do carrinho (Total Acumulado, Restantes, Estimado)
- Agrupamento por seções/corredores para navegação física na loja
- Sincronização em tempo real contínua (AC-027) com resiliência offline (AC-028)
- Abertura do modal de fechamento no caixa com geração de despesa (AC-029)
"""
from __future__ import annotations

import threading
from typing import Any, Callable
import flet as ft

from services.shopping_service import (
    get_all_items,
    get_items_grouped_by_corridor,
    calculate_cart_metrics,
    toggle_item_status,
)
from db.shopping import update_shopping_item
from services.shopping_realtime import ShoppingRealtimeSync
from services.price_scanner_service import extract_price_from_file_path, extract_price_from_base64
from ui.components.shopping_item_card import build_shopping_item_card
from ui.components.shopping_finish_modal import open_shopping_finish_modal
from ui.components.shopping_add_item_modal import open_shopping_add_item_modal
from ui.nav import toggle_theme, get_current_theme
from ui.theme import get_tokens, format_brl


class ShoppingMarketModeView(ft.Container):
    """View do Modo Mercado para uso físico na loja."""

    def __init__(
        self,
        page: ft.Page,
        market_name: str | None,
        on_exit_market_mode: Callable[[], None],
    ) -> None:
        super().__init__()
        self.page_ref = page
        self.market_name = market_name
        self.on_exit_market_mode = on_exit_market_mode

        self.expand = True
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)
        self.bgcolor = self.T["pageBg"]
        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8)

        self.items: list[dict[str, Any]] = []

        # Realtime Sync ativo a cada 2.5s no mercado
        self.realtime_sync = ShoppingRealtimeSync(
            on_change_callback=self._handle_realtime_update,
            interval_seconds=2.5,
        )

        self.file_picker = ft.FilePicker()
        if hasattr(self.page_ref, "services") and isinstance(self.page_ref.services, list):
            if self.file_picker not in self.page_ref.services:
                self.page_ref.services.append(self.file_picker)

        self._build_ui()

    def did_mount(self) -> None:
        """Carrega itens, oculta FAB e conecta realtime."""
        if hasattr(self.page_ref, "floating_action_button"):
            self.page_ref.floating_action_button = None

        if hasattr(self.page_ref, "services") and isinstance(self.page_ref.services, list):
            if self.file_picker not in self.page_ref.services:
                self.page_ref.services.append(self.file_picker)

        self.load_data()
        self.realtime_sync.start()


    def will_unmount(self) -> None:
        """Desconecta sincronização realtime ao sair do modo mercado."""
        self.realtime_sync.stop()

    def load_data(self) -> None:
        """Recarrega a lista do banco ou cache offline."""
        self.items = get_all_items()
        self.realtime_sync.trigger_local_update(self.items)
        self._update_metrics_and_list()
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _handle_realtime_update(self, new_items: list[dict[str, Any]]) -> None:
        """Atualização remota recebida do outro cônjuge."""
        self.items = new_items
        self._update_metrics_and_list()
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _build_ui(self) -> None:
        # Header do Modo Mercado
        btn_exit = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=self.T["textMuted"],
            tooltip="Sair do Modo Mercado",
            on_click=lambda _: self.on_exit_market_mode(),
        )

        market_display_name = self.market_name or "Mercado Geral"
        title_box = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCAL_MALL, size=18, color=self.T["success"]),
                        ft.Text("Modo Mercado", size=16, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"]),
                    ],
                    spacing=4,
                ),
                ft.Text(f"Loja: {market_display_name}", size=11, color=self.T["accent"]),
            ],
            spacing=1,
        )

        header_row = ft.Row(
            [title_box, btn_exit],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Card Proeminente de Métricas do Carrinho (AC-026)
        self.val_carrinho = ft.Text("R$ 0,00", size=22, weight=ft.FontWeight.BOLD, color=self.T["success"])
        self.val_progresso = ft.Text("0 de 0 itens", size=12, color=self.T["textPrimary"], weight=ft.FontWeight.W_600)
        self.val_restante = ft.Text("Restante estimado: R$ 0,00", size=11, color=self.T["textMuted"])

        self.progress_bar = ft.ProgressBar(value=0.0, color=self.T["success"], bgcolor=self.T["borderSubtle"], height=6)

        self.cart_metrics_box = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("NO CARRINHO", size=10, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                                    self.val_carrinho,
                                ],
                                spacing=2,
                            ),
                            ft.Column(
                                [
                                    self.val_progresso,
                                    self.val_restante,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.progress_bar,
                ],
                spacing=8,
            ),
            bgcolor=self.T["surfaceSolid"] if self.theme_mode == "dark" else "#FFFFFF",
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=10,
            padding=ft.Padding.all(12),
        )

        # Botão Fixo de Finalização no Caixa (AC-029)
        self.btn_finish = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.POINT_OF_SALE, size=20, color="#08090F"),
                    ft.Text("FINALIZAR COMPRA NO CAIXA", size=13, weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            ),
            height=46,
            on_click=lambda _: self._open_finish_dialog(),
        )

        # Lista de corredores e itens
        self.items_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        self.content = ft.Column(
            [
                header_row,
                self.cart_metrics_box,
                self.items_col,
                self.btn_finish,
            ],
            spacing=10,
            expand=True,
        )

    def _handle_toggle_item(self, item_id: str, is_bought: bool) -> None:
        """Marca ou desmarca item como comprado com suporte offline."""
        toggle_item_status(item_id, is_bought)
        # Atualiza estado local imediatamente
        for it in self.items:
            if it.get("id") == item_id:
                it["is_bought"] = is_bought
                break
        self.realtime_sync.trigger_local_update(self.items)
        self._update_metrics_and_list()
        self.page_ref.update()

    def _handle_edit_item(self, item: dict[str, Any]) -> None:
        """Abre o diálogo de edição do item selecionado no modo mercado."""
        open_shopping_add_item_modal(
            page=self.page_ref,
            on_item_added=lambda _: self.load_data(),
            current_market=self.market_name,
            item_to_edit=item,
        )

    def _handle_scan_price(self, item: dict[str, Any]) -> None:
        """Aciona a câmera/seletor para fotografar a etiqueta de gôndola e ler o preço."""
        item_name = item.get("name", "Produto")

        async def _pick_and_scan():
            try:
                files = await self.file_picker.pick_files(
                    dialog_title=f"Fotografar Etiqueta: {item_name}",
                    file_type=ft.FilePickerFileType.IMAGE,
                    allow_multiple=False,
                )
                if not files:
                    return

                picked_file = files[0]
                self._show_snack(f"Lendo etiqueta de '{item_name}' com IA...")

                def _process_image():
                    import base64
                    res: dict[str, Any] = {"success": False}
                    try:
                        if getattr(picked_file, "path", None):
                            res = extract_price_from_file_path(picked_file.path, item_name=item_name)
                        elif getattr(picked_file, "bytes", None):
                            b64 = base64.b64encode(picked_file.bytes).decode("utf-8")
                            res = extract_price_from_base64(b64, item_name=item_name)
                    except Exception as ex:
                        res = {"success": False, "error": str(ex)}

                    def _update_ui():
                        if res.get("success") and res.get("price") is not None:
                            new_price = float(res["price"])
                            # No modo mercado, atualiza preço real e marca como no carrinho
                            update_shopping_item(item["id"], {
                                "actual_price": new_price,
                                "estimated_price": new_price,
                                "is_bought": True,
                            })
                            self.load_data()
                            self._show_snack(f"✅ {item_name}: {format_brl(new_price)} adicionado ao carrinho!")
                        else:
                            err_msg = res.get("error") or "Preço não identificado na foto"
                            self._show_snack(f"⚠️ {err_msg}. Tente aproximar a foto da etiqueta.")

                    if hasattr(self.page_ref, "run_thread"):
                        self.page_ref.run_thread(_update_ui)
                    else:
                        _update_ui()

                threading.Thread(target=_process_image, daemon=True).start()

            except Exception as ex:
                self._show_snack(f"Não foi possível abrir o seletor/câmera: {ex}")

        if hasattr(self.page_ref, "run_task"):
            self.page_ref.run_task(_pick_and_scan)

    def _show_snack(self, message: str) -> None:
        """Exibe mensagem de feedback rápido na tela."""
        snack = ft.SnackBar(
            content=ft.Text(message, color="#08090F", weight=ft.FontWeight.BOLD),
            bgcolor=self.T["accent"],
            duration=3000,
        )
        self.page_ref.snack_bar = snack
        snack.open = True
        self.page_ref.update()

    def _update_metrics_and_list(self) -> None:
        """Recalcula totais do carrinho e recarrega os cards agrupados."""
        metrics = calculate_cart_metrics(self.items)

        self.val_carrinho.value = format_brl(metrics["total_bought_amount"])
        self.val_progresso.value = f"{metrics['bought_count']} de {metrics['total_count']} itens comprados"
        self.val_restante.value = f"Faltam: {format_brl(metrics['total_pending_amount'])}"
        self.progress_bar.value = (metrics["completion_pct"] / 100.0) if metrics["total_count"] > 0 else 0.0

        grouped = get_items_grouped_by_corridor(self.items)
        controls: list[ft.Control] = []

        for corridor_name, corridor_items in grouped.items():
            # Conta quantos faltam no corredor
            corridor_pending = sum(1 for it in corridor_items if not it.get("is_bought"))
            badge_text = f"{corridor_pending} pendente(s)" if corridor_pending > 0 else "Concluído"
            badge_color = self.T["warning"] if corridor_pending > 0 else self.T["success"]

            header = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(corridor_name.upper(), size=11, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"]),
                        ft.Text(f"• {badge_text}", size=11, color=badge_color, weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding.only(top=6, bottom=2),
            )
            controls.append(header)

            for item in corridor_items:
                card = build_shopping_item_card(
                    item=item,
                    theme_mode=self.theme_mode,
                    on_toggle=self._handle_toggle_item,
                    on_edit=self._handle_edit_item,
                    on_scan_price=self._handle_scan_price,
                    is_market_mode=True,
                )
                controls.append(card)

        self.items_col.controls = controls

    def _open_finish_dialog(self) -> None:
        """Abre modal de fechamento no caixa para gerar despesa."""
        bought_items = [it for it in self.items if it.get("is_bought")]
        if not bought_items:
            snack = ft.SnackBar(
                content=ft.Text("Marque pelo menos um item com 'OK' antes de finalizar!", color="#08090F"),
                bgcolor=self.T["warning"],
            )
            self.page_ref.snack_bar = snack
            snack.open = True
            self.page_ref.update()
            return

        metrics = calculate_cart_metrics(self.items)
        total_calc = metrics["total_bought_amount"]

        def on_done():
            self.on_exit_market_mode()

        open_shopping_finish_modal(
            page=self.page_ref,
            bought_items=bought_items,
            market_name=self.market_name,
            total_calculated=total_calc,
            on_completed=on_done,
        )
