"""
app.py — Entrypoint do MAI Finance Flet Web App.

Execução local:
    flet run app.py --web --port 8550

Execução em Docker:
    CMD ["python", "app.py"]
"""
import os
import sys
import warnings

# Suprime avisos de depreciação de bibliotecas de terceiros (Flet 1.0 e Supabase)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Garante que o diretório atual está no sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft

import config  # noqa: F401
from db.auth import verify_token
from ui.auth_view import AuthView
from ui.categories_modal import open_categories_modal
from ui.clone_month_modal import open_clone_month_modal
from ui.backup_modal import open_backup_modal
from ui.dashboard_view import DashboardView
from ui.theme import month_label
from ui.storage_util import get_local_item, remove_local_item


def main(page: ft.Page) -> None:
    page.title = "MAI Finance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#08090F"
    page.padding = 0
    page.fonts = {
        "Inter": "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
    }
    page.theme = ft.Theme(font_family="Inter")

    current_dashboard: DashboardView | None = None

    def show_auth() -> None:
        nonlocal current_dashboard
        if current_dashboard is not None:
            try:
                current_dashboard.will_unmount()
            except Exception:
                pass
            current_dashboard = None
        if hasattr(page, "floating_action_button"):
            page.floating_action_button = None
        page.on_resize = None
        page.controls.clear()
        auth_view = AuthView(
            page=page,
            on_login_success=lambda token, user: show_dashboard(),
        )
        page.add(
            ft.SafeArea(
                content=auth_view,
                avoid_intrusions_top=True,
                avoid_intrusions_bottom=True,
                expand=True,
            )
        )
        page.update()

    def handle_logout() -> None:
        nonlocal current_dashboard
        if current_dashboard is not None:
            try:
                current_dashboard.will_unmount()
            except Exception:
                pass
            current_dashboard = None
        if hasattr(page, "floating_action_button"):
            page.floating_action_button = None
        page.on_resize = None
        remove_local_item(page, "auth_token")
        remove_local_item(page, "user_data")
        show_auth()

    def show_dashboard() -> None:
        nonlocal current_dashboard
        try:
            if current_dashboard is not None:
                try:
                    current_dashboard.will_unmount()
                except Exception:
                    pass
            page.controls.clear()
            dashboard = DashboardView(
                page=page,
                on_logout=handle_logout,
                on_open_categories=lambda: open_categories_modal(page, on_changed=dashboard.load_data),
                on_open_clone_month=lambda: open_clone_month_modal(
                    page,
                    current_month_ref=dashboard.current_month_ref,
                    on_cloned=lambda target_m, count=0: _on_cloned_redirect(dashboard, target_m, count),
                ),
                on_open_backups=lambda: open_backup_modal(page, on_restored=dashboard.load_data),
            )
            current_dashboard = dashboard
            page.on_resize = dashboard._handle_page_resized
            page.add(
                ft.SafeArea(
                    content=dashboard,
                    avoid_intrusions_top=True,
                    avoid_intrusions_bottom=True,
                    expand=True,
                )
            )
            page.update()
            dashboard.did_mount()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"[app.py] Erro ao carregar Dashboard: {exc}")

    def _on_cloned_redirect(dashboard: DashboardView, target_month: str, count: int = 0) -> None:
        clean_target = target_month[:7]
        dashboard.current_month_ref = clean_target
        dashboard.month_display.value = month_label(clean_target)
        dashboard.load_data()
        msg = f"{count} despesa(s) clonada(s) para {month_label(clean_target)} com sucesso!" if count else f"Despesas clonadas para {month_label(clean_target)} com sucesso!"
        dashboard._show_snack(msg)

    # Verifica sessão existente
    token = get_local_item(page, "auth_token")
    if token:
        payload = verify_token(token)
        if payload:
            show_dashboard()
            return

    show_auth()


def _open_placeholder_modal(page: ft.Page, feature_name: str) -> None:
    dlg = ft.AlertDialog(
        title=ft.Text(feature_name),
        content=ft.Text(f"O módulo '{feature_name}' será carregado na respectiva etapa da migração."),
        actions=[
            ft.Button(
                content=ft.Text("Fechar"),
                on_click=lambda _: _close_dialog(page, dlg),
            )
        ],
    )
    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.dialog = dlg
        dlg.open = True
        page.update()


def _close_dialog(page: ft.Page, dlg: ft.AlertDialog) -> None:
    dlg.open = False
    if hasattr(page, "pop_dialog"):
        try:
            page.pop_dialog()
        except Exception:
            pass
    page.update()


if __name__ == "__main__":
    assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host=config.FLET_HOST,
        port=config.FLET_PORT,
        assets_dir=assets_path,
    )

