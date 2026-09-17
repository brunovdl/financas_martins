"""
backup_modal.py — Modal de gerenciamento e restauração de backups do MAI Finance.

Implementa:
- Listagem dos snapshots históricos de backup (AC-014)
- Disparo de backup manual via RPC do Supabase (AC-014)
- Restauração com diálogo de confirmação (AC-015)
- Feedback visual de progresso e sucesso
"""
from __future__ import annotations

from typing import Any, Callable
import flet as ft

from services.backups import (
    list_backups,
    create_manual_backup,
    restore_backup,
)
from ui.theme import get_tokens, format_brl


class BackupModal(ft.AlertDialog):
    """Diálogo modal para criação e restauração de backups."""

    def __init__(
        self,
        page: ft.Page,
        on_restored: Callable[[], None] | None = None,
    ) -> None:
        self.page_ref = page
        self.on_restored = on_restored
        self.T = get_tokens("dark")

        self.backups: list[dict[str, Any]] = []
        self.is_creating = False

        self.status_msg = ft.Text("", size=12, color=self.T["textMuted"])
        self.backups_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=260)
        self.spinner = ft.ProgressRing(width=20, height=20, color=self.T["accent"], visible=False)

        self.btn_create = ft.Button(
            content=ft.Row(
                [
                    self.spinner,
                    ft.Icon(ft.Icons.BACKUP, size=16, color="#08090F"),
                    ft.Text("Criar Backup Manual", weight=ft.FontWeight.BOLD, color="#08090F"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(bgcolor=self.T["accent"]),
            on_click=self._handle_create_backup,
        )

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0
        modal_w = min(page_w - 32, 500)

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.btn_create, self.status_msg], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color=self.T["borderSubtle"], height=1),
                    ft.Text("Histórico de Backups", size=13, weight=ft.FontWeight.BOLD, color=self.T["textMuted"]),
                    self.backups_list_col,
                ],
                spacing=12,
                tight=True,
            ),
            width=modal_w,
        )

        super().__init__(
            title=ft.Text("Backups do Sistema", weight=ft.FontWeight.BOLD, size=18),
            content=content,
            actions=[
                ft.Button(content=ft.Text("Fechar"), on_click=lambda _: self._close()),
            ],
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
                ft.Text("Nenhum backup encontrado.", size=12, color=self.T["textMuted"])
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

        type_badge = ft.Container(
            content=ft.Text(btype.upper(), size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            bgcolor=self.T["accent"] if btype == "manual" else "#475569",
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        info_col = ft.Column(
            [
                ft.Row([type_badge, ft.Text(created_at, size=13, weight=ft.FontWeight.BOLD, color=self.T["textPrimary"])], spacing=6),
                ft.Text(f"{cats_cnt} categorias, {exps_cnt} despesas • {format_brl(total_amt)}", size=11, color=self.T["textMuted"]),
            ],
            spacing=2,
            expand=True,
        )

        btn_restore = ft.Button(
            content=ft.Text("Restaurar", size=12, color=self.T["warning"]),
            style=ft.ButtonStyle(
                bgcolor=self.T["surface"],
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ),
            on_click=lambda _, item_id=bid, dt=created_at: self._confirm_restore(item_id, dt),
        )

        return ft.Container(
            content=ft.Row([info_col, btn_restore], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=self.T["surfaceSolid"],
            border=ft.Border.all(1, self.T["borderSubtle"]),
            border_radius=8,
            padding=ft.Padding.all(10),
        )

    def _handle_create_backup(self, _: ft.ControlEvent) -> None:
        self.spinner.visible = True
        self.btn_create.disabled = True
        self.status_msg.value = "Gerando snapshot..."
        self.page_ref.update()

        try:
            create_manual_backup()
            self.status_msg.value = "Backup manual gerado com sucesso!"
            self.status_msg.color = self.T["success"]
            self._load_backups()
        except Exception as exc:
            self.status_msg.value = f"Erro ao criar backup: {exc}"
            self.status_msg.color = self.T["danger"]
        finally:
            self.spinner.visible = False
            self.btn_create.disabled = False
            self.page_ref.update()

    def _confirm_restore(self, backup_id: str, date_str: str) -> None:
        confirm_dlg = ft.AlertDialog(
            title=ft.Text("Restaurar Snapshot"),
            content=ft.Text(
                f"ATENÇÃO: Restaurar o backup de '{date_str}' irá SOBRESCREVER "
                "todas as categorias e despesas atuais pelos dados deste snapshot.\n\n"
                "Deseja continuar?"
            ),
            actions=[
                ft.Button(content=ft.Text("Cancelar"), on_click=lambda _: self._close_dialog(confirm_dlg)),
                ft.Button(
                    content=ft.Text("Restaurar Agora", color=self.T["danger"], weight=ft.FontWeight.BOLD),
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
        self.status_msg.value = "Restaurando snapshot no banco..."
        self.status_msg.color = self.T["warning"]
        self.page_ref.update()

        try:
            res = restore_backup(backup_id)
            self.status_msg.value = f"Restaurado com sucesso: {res['categories_restored']} cats, {res['expenses_restored']} despesas."
            self.status_msg.color = self.T["success"]
            self._close()
            if self.on_restored:
                self.on_restored()
        except Exception as exc:
            self.status_msg.value = f"Erro na restauração: {exc}"
            self.status_msg.color = self.T["danger"]
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


def open_backup_modal(page: ft.Page, on_restored: Callable[[], None] | None = None) -> None:
    modal = BackupModal(page=page, on_restored=on_restored)
    if hasattr(page, "show_dialog"):
        page.show_dialog(modal)
    else:
        page.dialog = modal
        modal.open = True
        page.update()
