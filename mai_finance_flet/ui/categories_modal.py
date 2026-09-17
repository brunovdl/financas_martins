"""
categories_modal.py — Modal de gerenciamento de categorias do MAI Finance.
Segue rigorosamente o Design System oficial e padrão de modais (Gold Standard).
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from services.categories import (
    list_categories,
    create_category,
    update_category,
    delete_category,
)
from ui.nav import get_current_theme
from ui.theme import get_tokens, get_badge_colors
from ui.components.modal_header import build_modal_header
from ui.components.mai_loading import MaiLoading

COLOR_PALETTE = [
    "#94A3B8",  # Slate
    "#5EA8F2",  # Blue
    "#B399F5",  # Purple
    "#F5738C",  # Pink
    "#F2B84B",  # Amber
    "#3FD6C4",  # Teal
    "#10B981",  # Emerald
    "#F97316",  # Orange
    "#EC4899",  # Rose
    "#8B5CF6",  # Violet
]


class CategoriesModal(ft.AlertDialog):
    """Diálogo modal para gerenciamento completo de categorias."""

    def __init__(
        self,
        page: ft.Page,
        on_categories_changed: Callable[[], None] | None = None,
    ) -> None:
        self.page_ref = page
        self.on_categories_changed = on_categories_changed

        # Detecção dinâmica de tema (Light / Dark)
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)
        self.categories: list[dict[str, Any]] = []

        # Superfície de cards internos adaptada ao tema
        self.card_bg = "#F8FAFC" if self.theme_mode == "light" else self.T["surfaceSolid"]
        self.card_border = ft.Border.all(1, self.T["borderSubtle"])

        # Estado do formulário
        self.selected_color = COLOR_PALETTE[0]
        self.editing_id: str | None = None

        # Controles de UI
        self.error_text = ft.Text("", color=self.T["danger"], size=12, visible=False)

        self.name_field = ft.TextField(
            label="Nome da Categoria",
            hint_text="Ex: Alimentação, Lazer...",
            dense=True,
            bgcolor=self.T["surface"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            expand=True,
            on_submit=self._handle_save,
        )

        self.palette_row = ft.Row(spacing=6, wrap=True)
        self.color_hex_field = ft.TextField(
            label="Hex",
            value=self.selected_color,
            width=95,
            dense=True,
            bgcolor=self.T["surface"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            text_size=12,
            on_change=self._on_hex_field_change,
        )
        self._build_palette_controls()

        self.btn_save = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ADD, size=16, color="#08090F"),
                    ft.Text("Adicionar", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=4,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self._handle_save,
        )

        self.btn_cancel_edit = ft.Button(
            content=ft.Text("Cancelar", color=self.T["textMuted"], size=12),
            style=ft.ButtonStyle(
                bgcolor=self.T["surface"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            visible=False,
            on_click=self._cancel_edit,
        )

        # Formulário Compacto com Superfície Adaptada ao Tema
        form_container = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self.name_field, self.btn_save, self.btn_cancel_edit],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Selecione a cor:", size=11, weight=ft.FontWeight.W_500, color=self.T["textMuted"]),
                                    self.palette_row,
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            self.color_hex_field,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    self.error_text,
                ],
                spacing=8,
            ),
            bgcolor=self.card_bg,
            border=self.card_border,
            border_radius=12,
            padding=12,
        )

        self.categories_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=270)

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 450)

        # Cabeçalho unificado com Logo da Marca e Fechar 'X'
        modal_header = build_modal_header(
            title="Gerenciar Categorias",
            on_close=self._close,
            theme_tokens=self.T,
        )

        main_content = ft.Container(
            content=ft.Column(
                [
                    form_container,
                    ft.Row(
                        [
                            ft.Text("Categorias Existentes", size=13, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    self.categories_list,
                ],
                spacing=12,
                tight=True,
            ),
            width=modal_w,
        )

        self.btn_close_footer = ft.Button(
            content=ft.Text("Fechar", color=self.T["textMuted"]),
            style=ft.ButtonStyle(
                bgcolor=self.T["surfaceSolid"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._close(),
        )

        super().__init__(
            title=modal_header,
            content=main_content,
            bgcolor=self.T["surface"],
            actions=[self.btn_close_footer],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._load_categories()

    def _on_hex_field_change(self, e: ft.ControlEvent) -> None:
        val = (e.control.value or "").strip()
        if not val.startswith("#"):
            val = f"#{val}"
        if len(val) in (4, 7):
            self.selected_color = val
            self._build_palette_controls()
            self.page_ref.update()

    def _build_palette_controls(self) -> None:
        self.palette_row.controls.clear()
        border_highlight = "#0F172A" if self.theme_mode == "light" else "#FFFFFF"
        for color_hex in COLOR_PALETTE:
            is_selected = color_hex.lower() == self.selected_color.lower()
            btn = ft.Container(
                width=24,
                height=24,
                border_radius=12,
                bgcolor=color_hex,
                border=ft.Border.all(2.5, border_highlight) if is_selected else ft.Border.all(1, "rgba(0,0,0,0.1)"),
                on_click=lambda _, c=color_hex: self._select_color(c),
                ink=True,
                tooltip=color_hex,
            )
            self.palette_row.controls.append(btn)

    def _select_color(self, color_hex: str) -> None:
        self.selected_color = color_hex
        self.color_hex_field.value = color_hex
        self._build_palette_controls()
        self.page_ref.update()

    def _load_categories(self) -> None:
        try:
            self.categories = list_categories()
        except Exception:
            self.categories = []

        self.categories_list.controls.clear()
        if not self.categories:
            self.categories_list.controls.append(
                ft.Container(
                    content=ft.Text("Nenhuma categoria cadastrada.", size=12, color=self.T["textMuted"]),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )
        else:
            for cat in self.categories:
                self.categories_list.controls.append(self._build_category_item(cat))

        if self.page_ref:
            self.page_ref.update()

    def _build_category_item(self, cat: dict[str, Any]) -> ft.Container:
        cat_id = cat.get("id", "")
        name = cat.get("name", "")
        color = cat.get("color") or cat.get("color_hex") or "#94A3B8"

        # Badge com contraste perfeito garantido para Dark e Light Mode
        bg_badge, fg_badge, border_badge = get_badge_colors(color, is_light=self.theme_mode == "light")

        badge = ft.Container(
            content=ft.Text(name, size=12, weight=ft.FontWeight.W_600, color=fg_badge),
            bgcolor=bg_badge,
            border=ft.Border.all(1, border_badge) if border_badge else None,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        )

        btn_edit = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=16,
            icon_color=self.T["textMuted"],
            tooltip="Editar",
            on_click=lambda _, c=cat: self._start_edit(c),
        )

        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=16,
            icon_color=self.T["danger"],
            tooltip="Excluir",
            on_click=lambda _, cid=cat_id, cname=name: self._confirm_delete(cid, cname),
        )

        return ft.Container(
            content=ft.Row(
                [
                    badge,
                    ft.Row([btn_edit, btn_delete], spacing=0),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.card_bg,
            border=self.card_border,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        )

    def _start_edit(self, cat: dict[str, Any]) -> None:
        self.editing_id = cat.get("id")
        self.name_field.value = cat.get("name", "")
        col = cat.get("color") or cat.get("color_hex") or COLOR_PALETTE[0]
        self.selected_color = col
        self.color_hex_field.value = col
        self.btn_save.content = ft.Row(
            [
                ft.Icon(ft.Icons.CHECK, size=16, color="#08090F"),
                ft.Text("Salvar", weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=4,
            tight=True,
        )
        self.btn_cancel_edit.visible = True
        self.error_text.visible = False
        self._build_palette_controls()
        self.page_ref.update()

    def _cancel_edit(self, _: ft.ControlEvent | None = None) -> None:
        self.editing_id = None
        self.name_field.value = ""
        self.selected_color = COLOR_PALETTE[0]
        self.color_hex_field.value = COLOR_PALETTE[0]
        self.btn_save.content = ft.Row(
            [
                ft.Icon(ft.Icons.ADD, size=16, color="#08090F"),
                ft.Text("Adicionar", weight=ft.FontWeight.BOLD, color="#08090F"),
            ],
            spacing=4,
            tight=True,
        )
        self.btn_cancel_edit.visible = False
        self.error_text.visible = False
        self._build_palette_controls()
        self.page_ref.update()

    def _handle_save(self, _: ft.ControlEvent) -> None:
        name = (self.name_field.value or "").strip()
        if not name:
            self.error_text.value = "O nome da categoria é obrigatório."
            self.error_text.visible = True
            self.page_ref.update()
            return

        self.error_text.visible = False
        try:
            if self.editing_id:
                update_category(self.editing_id, name, self.selected_color)
                self._cancel_edit(None)
            else:
                create_category(name, self.selected_color)
                self.name_field.value = ""

            self._load_categories()
            if self.on_categories_changed:
                self.on_categories_changed()
        except Exception as exc:
            self.error_text.value = str(exc)
            self.error_text.visible = True
            self.page_ref.update()

    def _confirm_delete(self, category_id: str, category_name: str) -> None:
        confirm_header = build_modal_header(
            title="Excluir Categoria",
            on_close=lambda: self._close_dialog(confirm_dlg),
            theme_tokens=self.T,
        )
        confirm_dlg = ft.AlertDialog(
            title=confirm_header,
            content=ft.Container(
                content=ft.Text(
                    f"Tem certeza que deseja excluir '{category_name}'?\n\n"
                    "As despesas vinculadas não serão apagadas, apenas ficarão sem categoria definida.",
                    size=13,
                    color=self.T["textPrimary"],
                ),
                width=340,
            ),
            bgcolor=self.T["surface"],
            actions=[
                ft.Button(
                    content=ft.Text("Cancelar", color=self.T["textMuted"]),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["surfaceSolid"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._close_dialog(confirm_dlg),
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
                    on_click=lambda _: self._execute_delete(confirm_dlg, category_id),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if hasattr(self.page_ref, "show_dialog"):
            self.page_ref.show_dialog(confirm_dlg)
        else:
            self.page_ref.dialog = confirm_dlg
            confirm_dlg.open = True
            self.page_ref.update()

    def _execute_delete(self, confirm_dlg: ft.AlertDialog, category_id: str) -> None:
        self._close_dialog(confirm_dlg)
        try:
            delete_category(category_id)
            self._load_categories()
            if self.on_categories_changed:
                self.on_categories_changed()
        except Exception as exc:
            self.error_text.value = f"Erro ao excluir: {exc}"
            self.error_text.visible = True
            self.page_ref.update()

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        if hasattr(self.page_ref, "pop_dialog"):
            try:
                self.page_ref.pop_dialog()
            except Exception:
                pass
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


def open_categories_modal(page: ft.Page, on_changed: Callable[[], None] | None = None) -> None:
    """Função utilitária para instanciar e abrir o modal de categorias."""
    modal = CategoriesModal(page=page, on_categories_changed=on_changed)
    if hasattr(page, "show_dialog"):
        page.show_dialog(modal)
    else:
        page.dialog = modal
        modal.open = True
        page.update()
