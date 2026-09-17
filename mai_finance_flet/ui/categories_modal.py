"""
categories_modal.py — Modal de gerenciamento de categorias do MAI Finance.

Implementa:
- Listagem de categorias existentes (AC-010)
- Criação de nova categoria com seleção de cor hex (AC-010)
- Edição de nome e cor de categoria existente
- Exclusão de categoria com diálogo de confirmação (AC-011)
- Validação de unicidade e feedback de erros inline
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
from ui.theme import get_tokens

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
        self.T = get_tokens("dark")
        self.categories: list[dict[str, Any]] = []

        # Estado do formulário
        self.selected_color = COLOR_PALETTE[0]
        self.editing_id: str | None = None

        # Controles de UI
        self.title_text = ft.Text("Gerenciar Categorias", weight=ft.FontWeight.BOLD, size=18)
        self.error_text = ft.Text("", color=self.T["danger"], size=12, visible=False)

        self.name_field = ft.TextField(
            label="Nome da Categoria",
            hint_text="Ex: Alimentação, Moradia...",
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            height=46,
            expand=True,
        )

        self.palette_row = ft.Row(spacing=6, wrap=True)
        self.color_hex_field = ft.TextField(
            label="Cor Hex",
            value=self.selected_color,
            width=110,
            height=40,
            bgcolor=self.T["surfaceSolid"],
            border_color=self.T["borderSubtle"],
            focused_border_color=self.T["accent"],
            color=self.T["textPrimary"],
            border_radius=8,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
            text_size=12,
            on_change=self._on_hex_field_change,
        )
        self._build_palette_controls()

        self.btn_save = ft.Button(
            content=ft.Text("Adicionar", weight=ft.FontWeight.BOLD, color="#08090F"),
            style=ft.ButtonStyle(bgcolor=self.T["accent"]),
            on_click=self._handle_save,
        )

        self.btn_cancel_edit = ft.Button(
            content=ft.Text("Cancelar Edição"),
            visible=False,
            on_click=self._cancel_edit,
        )

        form_container = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.name_field, self.btn_save, self.btn_cancel_edit], alignment=ft.MainAxisAlignment.START),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Selecione a cor ou digite:", size=11, color=self.T["textMuted"]),
                                    self.palette_row,
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            self.color_hex_field,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    self.error_text,
                ],
                spacing=8,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=10,
            padding=12,
        )

        self.categories_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=280)

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 480)

        main_content = ft.Container(
            content=ft.Column(
                [
                    form_container,
                    ft.Text("Categorias Existentes", size=13, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                    self.categories_list,
                ],
                spacing=12,
                tight=True,
            ),
            width=modal_w,
        )

        super().__init__(
            title=self.title_text,
            content=main_content,
            actions=[
                ft.Button(
                    content=ft.Text("Fechar"),
                    on_click=lambda _: self._close(),
                ),
            ],
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
        for color_hex in COLOR_PALETTE:
            is_selected = color_hex.lower() == self.selected_color.lower()
            btn = ft.Container(
                width=26,
                height=26,
                border_radius=13,
                bgcolor=color_hex,
                border=ft.Border.all(2, "#FFFFFF" if is_selected else "transparent"),
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
                ft.Text("Nenhuma categoria cadastrada.", size=12, color=self.T["textMuted"])
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

        pill = ft.Container(
            content=ft.Text(name, size=12, weight=ft.FontWeight.W_500, color="#FFFFFF"),
            bgcolor=color,
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
                    pill,
                    ft.Row([btn_edit, btn_delete], spacing=2),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        )

    def _start_edit(self, cat: dict[str, Any]) -> None:
        self.editing_id = cat.get("id")
        self.name_field.value = cat.get("name", "")
        col = cat.get("color") or cat.get("color_hex") or COLOR_PALETTE[0]
        self.selected_color = col
        self.color_hex_field.value = col
        self.btn_save.content = ft.Text("Salvar", weight=ft.FontWeight.BOLD, color="#08090F")
        self.btn_cancel_edit.visible = True
        self.error_text.visible = False
        self._build_palette_controls()
        self.page_ref.update()

    def _cancel_edit(self, _: ft.ControlEvent) -> None:
        self.editing_id = None
        self.name_field.value = ""
        self.selected_color = COLOR_PALETTE[0]
        self.color_hex_field.value = COLOR_PALETTE[0]
        self.btn_save.content = ft.Text("Adicionar", weight=ft.FontWeight.BOLD, color="#08090F")
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
        confirm_dlg = ft.AlertDialog(
            title=ft.Text("Excluir Categoria"),
            content=ft.Text(
                f"Tem certeza que deseja excluir '{category_name}'?\n\n"
                "As despesas associadas NÃO serão apagadas (ficarão sem categoria definida)."
            ),
            actions=[
                ft.Button(
                    content=ft.Text("Cancelar"),
                    on_click=lambda _: self._close_dialog(confirm_dlg),
                ),
                ft.Button(
                    content=ft.Text("Excluir", color=self.T["danger"]),
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
        if hasattr(self.page_ref, "pop_dialog"):
            self.page_ref.pop_dialog()
        else:
            dlg.open = False
            self.page_ref.update()

    def _close(self) -> None:
        if hasattr(self.page_ref, "pop_dialog"):
            self.page_ref.pop_dialog()
        else:
            self.open = False
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
