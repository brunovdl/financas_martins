"""
clone_month_modal.py — Modal de Clonagem de Mês do MAI Finance.
Segue rigorosamente o Design System oficial e padrão de modais (Gold Standard).
"""
from __future__ import annotations

from typing import Callable
import flet as ft

from services.clone_month import clone_month
from ui.nav import get_current_theme
from ui.theme import get_tokens, month_label, shift_month, get_current_month_ref
from ui.components.modal_header import build_modal_header
from ui.components.mai_loading import MaiLoading


class CloneMonthModal(ft.AlertDialog):
    """Diálogo modal para clonagem de despesas entre meses."""

    def __init__(
        self,
        page: ft.Page,
        current_month_ref: str,
        on_cloned: Callable[[str, int], None] | None = None,
    ) -> None:
        self.page_ref = page
        self.on_cloned = on_cloned

        # Detecção dinâmica de tema (Light / Dark)
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)

        clean_ref = (current_month_ref or get_current_month_ref())[:7]
        self.current_month_ref = clean_ref

        # Meses de -12 até +12 a partir do mês atual do sistema
        self.month_options = []
        base = get_current_month_ref()
        for i in range(-12, 13):
            m = shift_month(base, i)
            self.month_options.append((m, month_label(m)))

        self.from_month = self.current_month_ref
        self.to_month = shift_month(self.current_month_ref, 1)

        # Dropdowns modernos e compactos com cores adaptadas ao tema
        self.from_dropdown = ft.Dropdown(
            label="Copiar despesas de:",
            options=[ft.dropdown.Option(key=m, text=lbl) for m, lbl in self.month_options],
            value=self.from_month,
            dense=True,
            width=330,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            on_select=self._on_from_change,
        )

        self.to_dropdown = ft.Dropdown(
            label="Colar despesas em:",
            options=[ft.dropdown.Option(key=m, text=lbl) for m, lbl in self.month_options],
            value=self.to_month,
            dense=True,
            width=330,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            on_select=self._on_to_change,
        )

        self.error_text = ft.Text("", color=self.T["danger"], size=12, visible=False)

        # Card de Seleção Visual dos Meses
        selector_card = ft.Container(
            content=ft.Column(
                controls=[
                    self.from_dropdown,
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.ARROW_DOWNWARD, color=self.T["accent"], size=18),
                                bgcolor=self.T["surface"],
                                border=ft.Border.all(1, self.T["borderSubtle"]),
                                border_radius=999,
                                padding=6,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.to_dropdown,
                ],
                spacing=8,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=12,
            padding=14,
        )

        # Botões de Ação Padronizados
        self.btn_cancel = ft.Button(
            content=ft.Text("Cancelar", color=self.T["textMuted"]),
            style=ft.ButtonStyle(
                bgcolor=self.T["surfaceSolid"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._close(),
        )

        self.btn_confirm = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.COPY_ALL_OUTLINED, size=16, color="#08090F"),
                    ft.Text("Clonar Despesas", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=6,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self._handle_clone,
        )

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 400)

        # Cabeçalho unificado com Logo da Marca e Fechar 'X'
        modal_header = build_modal_header(
            title="Clonar Despesas de um Mês",
            on_close=self._close,
            theme_tokens=self.T,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Duplique todas as despesas do mês selecionado para um novo período com status pendente e datas ajustadas.",
                        size=13,
                        color=self.T["textMuted"],
                    ),
                    selector_card,
                    self.error_text,
                ],
                spacing=12,
                tight=True,
            ),
            width=modal_w,
        )

        super().__init__(
            title=modal_header,
            content=content,
            bgcolor=self.T["surface"],
            actions=[
                self.btn_cancel,
                self.btn_confirm,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_from_change(self, e: ft.ControlEvent) -> None:
        val = None
        if hasattr(e, "control") and e.control and getattr(e.control, "value", None):
            val = e.control.value
        elif hasattr(e, "data") and e.data:
            val = e.data
        if val:
            cleaned = str(val).strip(' "\'')[:7]
            self.from_month = cleaned
            self.from_dropdown.value = cleaned

    def _on_to_change(self, e: ft.ControlEvent) -> None:
        val = None
        if hasattr(e, "control") and e.control and getattr(e.control, "value", None):
            val = e.control.value
        elif hasattr(e, "data") and e.data:
            val = e.data
        if val:
            cleaned = str(val).strip(' "\'')[:7]
            self.to_month = cleaned
            self.to_dropdown.value = cleaned

    def _handle_clone(self, _: ft.ControlEvent) -> None:
        raw_from = self.from_dropdown.value or self.from_month or ""
        raw_to = self.to_dropdown.value or self.to_month or ""

        from_m = str(raw_from).strip(' "\'')[:7]
        to_m = str(raw_to).strip(' "\'')[:7]

        if not from_m or not to_m:
            self.error_text.value = "Selecione o mês de origem e o mês de destino."
            self.error_text.visible = True
            self.page_ref.update()
            return

        if from_m == to_m:
            self.error_text.value = "O mês de origem e destino não podem ser iguais."
            self.error_text.visible = True
            self.page_ref.update()
            return

        self.error_text.visible = False
        self.btn_confirm.disabled = True
        self.btn_confirm.content = MaiLoading.button_spinner("Clonando...")
        self.page_ref.update()

        try:
            cloned = clone_month(from_m, to_m)
            if not cloned:
                self.error_text.value = f"Nenhuma despesa encontrada em {month_label(from_m)} para clonar."
                self.error_text.visible = True
                self.btn_confirm.disabled = False
                self.btn_confirm.content = ft.Row(
                    [
                        ft.Icon(ft.Icons.COPY_ALL_OUTLINED, size=16, color="#08090F"),
                        ft.Text("Clonar Despesas", weight=ft.FontWeight.BOLD, color="#08090F"),
                    ],
                    spacing=6,
                    tight=True,
                )
                self.page_ref.update()
                return

            # Fechamento determinístico e imediato
            self._close()
            if self.on_cloned:
                self.on_cloned(to_m, len(cloned))
        except Exception as exc:
            self.error_text.value = f"Erro ao clonar: {exc}"
            self.error_text.visible = True
            self.btn_confirm.disabled = False
            self.btn_confirm.content = ft.Row(
                [
                    ft.Icon(ft.Icons.COPY_ALL_OUTLINED, size=16, color="#08090F"),
                    ft.Text("Clonar Despesas", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=6,
                tight=True,
            )
            self.page_ref.update()

    def _close(self) -> None:
        self.open = False
        if hasattr(self.page_ref, "pop_dialog"):
            try:
                self.page_ref.pop_dialog()
            except Exception:
                pass
        if getattr(self.page_ref, "dialog", None) == self:
            self.page_ref.dialog = None
        self.page_ref.update()


def open_clone_month_modal(
    page: ft.Page,
    current_month_ref: str,
    on_cloned: Callable[[str, int], None] | None = None,
) -> None:
    modal = CloneMonthModal(page=page, current_month_ref=current_month_ref, on_cloned=on_cloned)
    if hasattr(page, "show_dialog"):
        page.show_dialog(modal)
    else:
        page.dialog = modal
        modal.open = True
        page.update()
