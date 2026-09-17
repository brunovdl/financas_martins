"""
clone_month_modal.py — Modal de Clonagem de Mês do MAI Finance.

Implementa:
- Seleção de mês de origem e destino (AC-012)
- Disparo da clonagem com ajuste de datas e reset de status
- Feedback visual e atualização pós-clonagem
"""
from __future__ import annotations

from typing import Callable
import flet as ft

from services.clone_month import clone_month
from ui.theme import get_tokens, month_label, shift_month, get_current_month_ref


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
        self.T = get_tokens("dark")
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

        # Dropdowns com largura explícita e tratamento de evento seguro
        self.from_dropdown = ft.Dropdown(
            label="Mês de Origem (Copiar de)",
            options=[ft.dropdown.Option(key=m, text=lbl) for m, lbl in self.month_options],
            value=self.from_month,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            width=330,
            on_select=self._on_from_change,
        )

        self.to_dropdown = ft.Dropdown(
            label="Mês de Destino (Colar em)",
            options=[ft.dropdown.Option(key=m, text=lbl) for m, lbl in self.month_options],
            value=self.to_month,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            width=330,
            on_select=self._on_to_change,
        )

        self.error_text = ft.Text("", color=self.T["danger"], size=12, visible=False)
        self.loading_spinner = ft.ProgressRing(width=20, height=20, color=self.T["accent"], visible=False)

        self.btn_confirm = ft.Button(
            content=ft.Row(
                [
                    self.loading_spinner,
                    ft.Text("Clonar Despesas", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(bgcolor=self.T["accent"]),
            on_click=self._handle_clone,
        )

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 350)

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Selecione o mês de origem e o mês de destino para duplicar as despesas recorrentes.",
                        size=13,
                        color=self.T["textPrimary"],
                    ),
                    ft.Text(
                        "As despesas serão recriadas com status 'pendente' e datas ajustadas.",
                        size=12,
                        color=self.T["textMuted"],
                    ),
                    self.from_dropdown,
                    ft.Icon(ft.Icons.ARROW_DOWNWARD, color=self.T["accent"], size=20),
                    self.to_dropdown,
                    self.error_text,
                ],
                spacing=12,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=modal_w,
        )

        super().__init__(
            title=ft.Text("Clonar Despesas de um Mês", weight=ft.FontWeight.BOLD, size=18),
            content=content,
            actions=[
                ft.Button(content=ft.Text("Cancelar"), on_click=lambda _: self._close()),
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
        self.loading_spinner.visible = True
        self.btn_confirm.disabled = True
        self.page_ref.update()

        try:
            cloned = clone_month(from_m, to_m)
            if not cloned:
                self.error_text.value = f"Nenhuma despesa encontrada em {month_label(from_m)} para clonar."
                self.error_text.visible = True
                self.loading_spinner.visible = False
                self.btn_confirm.disabled = False
                self.page_ref.update()
                return

            self._close()
            if self.on_cloned:
                self.on_cloned(to_m, len(cloned))
        except Exception as exc:
            self.error_text.value = f"Erro ao clonar: {exc}"
            self.error_text.visible = True
            self.loading_spinner.visible = False
            self.btn_confirm.disabled = False
            self.page_ref.update()

    def _close(self) -> None:
        if hasattr(self.page_ref, "pop_dialog"):
            self.page_ref.pop_dialog()
        else:
            self.open = False
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
