"""
update_modal.py — Modal Elegante de Notificação e Download de Atualizações do App Android
"""
import os
import threading
from typing import Any, Callable, Optional
import flet as ft
from ui.theme import get_tokens
from ui.components.modal_header import build_modal_header
from services.updater import download_apk, launch_apk_installer


def open_update_dialog(page: ft.Page, update_info: dict[str, Any]) -> None:
    """
    Exibe o diálogo padronizado de nova versão disponível com barra de progresso de download in-app.
    """
    is_light = getattr(page, "theme_mode", None) == ft.ThemeMode.LIGHT
    T = get_tokens("light" if is_light else "dark")

    current_ver = update_info.get("current_version", "1.0.0")
    latest_ver = update_info.get("latest_version", "1.0.1")
    download_url = update_info.get("download_url", "")
    apk_size_bytes = update_info.get("apk_size_bytes", 0)
    size_mb = f"{apk_size_bytes / (1024 * 1024):.1f} MB" if apk_size_bytes > 0 else ""
    release_notes = update_info.get("release_notes", "").strip() or "Melhorias de desempenho, correções e novas funcionalidades."

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=T["surface"],
        shape=ft.RoundedRectangleBorder(radius=12),
        content_padding=ft.Padding.all(0),
    )

    # Header oficial com logo da marca
    header = ft.Container(
        content=build_modal_header(
            title="Atualização Disponível",
            on_close=lambda: _close_dialog(page, dlg),
            theme_tokens=T,
        ),
        padding=ft.Padding.only(left=16, right=16, top=16, bottom=12),
    )

    # Elementos de Versão e Informações
    version_row = ft.Row(
        [
            ft.Container(
                content=ft.Text(f"Atual: v{current_ver}", size=12, color=T["textMuted"]),
                bgcolor=T["surfaceSolid"],
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                border=ft.Border.all(1, T["borderSubtle"]),
            ),
            ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=T.get("accent", "#3FD6C4")),
            ft.Container(
                content=ft.Text(f"Nova: v{latest_ver}", size=12, weight=ft.FontWeight.BOLD, color=T.get("accentOnBrand", "#08090F") if is_light else T.get("accent", "#3FD6C4")),
                bgcolor=T.get("accent", "#3FD6C4") if is_light else T.get("successBg", "#122620"),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                border=ft.Border.all(1, T.get("accent", "#3FD6C4")),
            ),
            ft.Text(size_mb, size=11, color=T["textMuted"]) if size_mb else ft.Container(),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    notes_box = ft.Container(
        content=ft.Column(
            [
                ft.Text("O que há de novo:", size=11, weight=ft.FontWeight.BOLD, color=T["textPrimary"]),
                ft.Text(
                    release_notes[:300] + ("..." if len(release_notes) > 300 else ""),
                    size=11,
                    color=T["textMuted"],
                    selectable=True,
                ),
            ],
            spacing=4,
        ),
        bgcolor=T["surfaceSolid"],
        border=ft.Border.all(1, T["borderSubtle"]),
        border_radius=8,
        padding=ft.Padding.all(10),
    )

    # Barra de Progresso de Download
    progress_bar = ft.ProgressBar(
        value=0.0,
        color=T["accent"],
        bgcolor=T["borderSubtle"],
        height=6,
        border_radius=ft.BorderRadius.all(3),
        visible=False,
    )
    status_text = ft.Text(
        "Toque em 'Atualizar Agora' para baixar e instalar.",
        size=11,
        color=T["textMuted"],
    )

    btn_cancel = ft.Button(
        content=ft.Text("Depois", color=T["textMuted"], size=13),
        style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT, elevation=0),
        on_click=lambda _: _close_dialog(page, dlg),
    )

    btn_update = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=16, color=T.get("accentOnBrand", "#08090F")),
                ft.Text("Atualizar Agora", size=13, weight=ft.FontWeight.BOLD, color=T.get("accentOnBrand", "#08090F")),
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor=T["accent"],
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        ),
    )

    actions_row = ft.Row(
        [btn_cancel, btn_update],
        alignment=ft.MainAxisAlignment.END,
        spacing=8,
    )

    file_info_text = ft.Text(
        "",
        size=10,
        color=T["textMuted"],
        selectable=True,
    )
    file_info_box = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=14, color=T["accent"]),
                ft.Column([file_info_text], spacing=0, expand=True),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=T["surfaceSolid"],
        border=ft.Border.all(1, T["borderSubtle"]),
        border_radius=6,
        padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        visible=False,
    )

    is_downloading = False

    def on_progress(pct: float, downloaded: int, total: int) -> None:
        progress_bar.value = pct
        down_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024) if total > 0 else 0
        status_text.value = f"Baixando: {int(pct * 100)}% ({down_mb:.1f} MB / {tot_mb:.1f} MB)"
        try:
            page.update()
        except Exception:
            pass

    def start_download(_: ft.ControlEvent) -> None:
        nonlocal is_downloading
        if is_downloading or not download_url:
            return
        is_downloading = True

        btn_update.disabled = True
        btn_cancel.disabled = True
        progress_bar.visible = True
        status_text.value = "Conectando ao servidor e iniciando download..."
        page.update()

        def _worker():
            try:
                apk_path = download_apk(download_url, progress_callback=on_progress)
                status_text.value = "✅ Download concluído com sucesso!"
                status_text.color = T.get("success", "#3FD6C4")
                status_text.weight = ft.FontWeight.BOLD

                file_info_text.value = f"Arquivo salvo em: {apk_path}"
                file_info_box.visible = True

                # Dispara tentativa automática de abertura do instalador nativo
                launch_apk_installer(page, apk_path, download_url)

                btn_install_apk = ft.Button(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INSTALL_MOBILE_ROUNDED, size=16, color=T.get("accentOnBrand", "#08090F")),
                            ft.Text("Instalar APK", size=13, weight=ft.FontWeight.BOLD, color=T.get("accentOnBrand", "#08090F")),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=T["accent"],
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ),
                    on_click=lambda _: launch_apk_installer(page, apk_path, download_url),
                )

                btn_browser = ft.Button(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.OPEN_IN_BROWSER, size=15, color=T.get("textPrimary", "#EDF0F7")),
                            ft.Text("Instalar pelo Navegador", size=12, color=T.get("textPrimary", "#EDF0F7")),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=T["surfaceSolid"],
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    ),
                    on_click=lambda _: page.launch_url(download_url),
                )

                btn_close_done = ft.Button(
                    content=ft.Text("Fechar", color=T["textMuted"], size=12),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT, elevation=0),
                    on_click=lambda _: _close_dialog(page, dlg),
                )

                actions_row.controls = [btn_close_done, btn_browser, btn_install_apk]
                actions_row.alignment = ft.MainAxisAlignment.END
                page.update()

            except Exception as exc:
                status_text.value = f"Erro no download: {exc}"
                status_text.color = T.get("danger", "#F5738C")
                btn_update.disabled = False
                btn_cancel.disabled = False
                progress_bar.visible = False
                page.update()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    btn_update.on_click = start_download

    dlg.content = ft.Container(
        content=ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            version_row,
                            notes_box,
                            progress_bar,
                            status_text,
                            file_info_box,
                            actions_row,
                        ],
                        spacing=12,
                    ),
                    padding=ft.Padding.only(left=16, right=16, bottom=16),
                ),
            ],
            spacing=0,
            tight=True,
        ),
        width=380,
    )

    _show_dialog(page, dlg)


def _show_dialog(page: ft.Page, dlg: ft.AlertDialog) -> None:
    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()


def _close_dialog(page: ft.Page, dlg: ft.AlertDialog) -> None:
    if hasattr(page, "pop_dialog"):
        page.pop_dialog()
    else:
        dlg.open = False
        page.update()
