"""
backup_modal.py — Modal de gerenciamento e restauração de backups do MAI Finance.
Segue rigorosamente o Design System oficial e padrão de modais (Gold Standard).
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from services.backups import (
    list_backups,
    create_manual_backup,
    restore_backup,
)
from ui.nav import get_current_theme
from ui.theme import get_tokens, format_brl
from ui.components.modal_header import build_modal_header
from ui.components.mai_loading import MaiLoading


class BackupModal(ft.AlertDialog):
    """Diálogo modal para criação e restauração de backups."""

    def __init__(
        self,
        page: ft.Page,
        on_restored: Callable[[], None] | None = None,
    ) -> None:
        self.page_ref = page
        self.on_restored = on_restored

        # Detecção dinâmica de tema (Light / Dark)
        self.theme_mode = get_current_theme(page)
        self.T = get_tokens(self.theme_mode)

        self.card_bg = "#F8FAFC" if self.theme_mode == "light" else self.T["surfaceSolid"]
        self.card_border = ft.Border.all(1, self.T["borderSubtle"])

        self.backups: list[dict[str, Any]] = []
        self.is_creating = False

        self.status_msg = ft.Text("", size=12, color=self.T["textMuted"])
        self.backups_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=270)

        # Botão Criar Backup Padronizado
        self.btn_create = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=16, color="#08090F"),
                    ft.Text("Criar Backup Manual", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=6,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["accent"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self._handle_create_backup,
        )

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 480)

        # Cabeçalho unificado com Logo da Marca e Fechar 'X'
        modal_header = build_modal_header(
            title="Backups do Sistema",
            on_close=self._close,
            theme_tokens=self.T,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.btn_create, self.status_msg], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(color=self.T["borderSubtle"], height=1),
                    ft.Row(
                        [
                            ft.Text("Histórico de Snapshots", size=13, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    self.backups_list_col,
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
            content=content,
            bgcolor=self.T["surface"],
            actions=[self.btn_close_footer],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._load_backups()

    def _load_backups(self) -> None:
        try:
            self.backups = list_backups()
        except Exception:
            self.backups = []

        self.backups_list_col.controls.clear()
        if not self.backups:
            self.backups_list_col.controls.append(
                ft.Container(
                    content=ft.Text("Nenhum backup encontrado.", size=12, color=self.T["textMuted"]),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )
        else:
            for b in self.backups:
                self.backups_list_col.controls.append(self._build_backup_row(b))

        if self.page_ref:
            self.page_ref.update()

    def _build_backup_row(self, b: dict[str, Any]) -> ft.Container:
        bid = b.get("id", "")
        btype = b.get("type", "automatico")
        created_at = str(b.get("created_at", ""))[:16].replace("T", " ")
        cats_cnt = b.get("categories_count", 0)
        exps_cnt = b.get("expenses_count", 0)
        total_amt = float(b.get("total_amount") or 0.0)

        is_manual = btype == "manual"
        badge_bg = self.T["successBg"] if is_manual else self.T["surface"]
        badge_fg = self.T["success"] if is_manual else self.T["textMuted"]
        badge_border = self.T["successBorder"] if is_manual else self.T["borderSubtle"]

        type_badge = ft.Container(
            content=ft.Text(btype.upper(), size=10, weight=ft.FontWeight.BOLD, color=badge_fg),
            bgcolor=badge_bg,
            border=ft.Border.all(1, badge_border),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        info_col = ft.Column(
            [
                ft.Row([type_badge, ft.Text(created_at, size=13, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"])], spacing=6),
                ft.Text(f"{cats_cnt} categorias, {exps_cnt} despesas • {format_brl(total_amt)}", size=11, color=self.T["textMuted"]),
            ],
            spacing=3,
            expand=True,
        )

        btn_restore = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.RESTORE, size=14, color=self.T["warning"]),
                    ft.Text("Restaurar", size=11, weight=ft.FontWeight.W_600, color=self.T["warning"]),
                ],
                spacing=4,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=self.T["warningBg"],
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            on_click=lambda _, item_id=bid, dt=created_at: self._confirm_restore(item_id, dt),
        )

        return ft.Container(
            content=ft.Row(
                [info_col, btn_restore],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=self.card_bg,
            border=self.card_border,
            border_radius=8,
            padding=ft.Padding.all(10),
        )

    def _handle_create_backup(self, _: ft.ControlEvent) -> None:
        self.btn_create.disabled = True
        self.btn_create.content = MaiLoading.button_spinner("Criando snapshot...")
        self.status_msg.value = "Gerando snapshot..."
        self.status_msg.color = self.T["textMuted"]
        self.page_ref.update()

        try:
            create_manual_backup()
            self.status_msg.value = "Backup gerado com sucesso!"
            self.status_msg.color = self.T["success"]
            self._load_backups()
        except Exception as exc:
            self.status_msg.value = f"Erro ao criar: {exc}"
            self.status_msg.color = self.T["danger"]
        finally:
            self.btn_create.disabled = False
            self.btn_create.content = ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=16, color="#08090F"),
                    ft.Text("Criar Backup Manual", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                spacing=6,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
            )
            self.page_ref.update()

    def _confirm_restore(self, backup_id: str, date_str: str) -> None:
        confirm_header = build_modal_header(
            title="Restaurar Snapshot",
            on_close=lambda: self._close_dialog(confirm_dlg),
            theme_tokens=self.T,
        )
        confirm_dlg = ft.AlertDialog(
            title=confirm_header,
            content=ft.Container(
                content=ft.Text(
                    f"ATENÇÃO: Restaurar o backup de '{date_str}' substituirá "
                    "todas as categorias e despesas atuais pelos dados gravados neste snapshot.\n\n"
                    "Deseja realmente continuar?",
                    size=13,
                    color=self.T["textPrimary"],
                ),
                width=350,
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
                            ft.Icon(ft.Icons.RESTORE, size=16, color="#FFFFFF"),
                            ft.Text("Restaurar Agora", weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=self.T["danger"],
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._execute_restore(confirm_dlg, backup_id),
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

    def _execute_restore(self, dlg: ft.AlertDialog, backup_id: str) -> None:
        self._close_dialog(dlg)
        self.status_msg.value = "Restaurando snapshot..."
        self.status_msg.color = self.T["warning"]
        self.page_ref.update()

        try:
            res = restore_backup(backup_id)
            self.status_msg.value = f"Restaurado com sucesso: {res.get('categories_restored', 0)} categorias, {res.get('expenses_restored', 0)} despesas."
            self.status_msg.color = self.T["success"]
            self._close()
            if self.on_restored:
                self.on_restored()
        except Exception as exc:
            self.status_msg.value = f"Erro na restauração: {exc}"
            self.status_msg.color = self.T["danger"]
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


def open_backup_modal(page: ft.Page, on_restored: Callable[[], None] | None = None) -> None:
    modal = BackupModal(page=page, on_restored=on_restored)
    if hasattr(page, "show_dialog"):
        page.show_dialog(modal)
    else:
        page.dialog = modal
        modal.open = True
        page.update()
