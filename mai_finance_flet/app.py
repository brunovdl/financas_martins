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

# Configura política do event loop para evitar WinError 10035 em sockets no Windows
if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Garante que o diretório atual está no sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft

import config  # noqa: F401
from db.auth import create_remember_token, verify_token
from ui.auth_view import AuthView
from ui.categories_modal import open_categories_modal
from ui.clone_month_modal import open_clone_month_modal
from ui.backup_modal import open_backup_modal
from ui.dashboard_view import DashboardView
from ui.shopping_view import ShoppingView
from ui.shopping_market_mode import ShoppingMarketModeView
from ui.theme import month_label
from ui.storage_util import (
    get_local_item,
    preload_local_items,
    purge_disk_cache,
    remove_local_item,
    set_local_items,
)

# Chaves de sessão persistidas no cliente (lidas no início de cada sessão)
SESSION_KEYS = [
    "auth_token",
    "user",
    "user_data",
    "remember_login",
    "remember_token",
    "saved_email",
    "saved_password",  # legado: só é lido para migrar e apagar
]


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
        for key in ("auth_token", "user", "user_data", "remember_token", "saved_password"):
            remove_local_item(page, key)
        show_auth()

    def show_dashboard() -> None:
        nonlocal current_dashboard
        try:
            if current_dashboard is not None:
                try:
                    current_dashboard.will_unmount()
                except Exception:
                    pass
            if hasattr(page, "overlay"):
                page.overlay.clear()
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
                on_open_shopping=show_shopping,
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

    def show_shopping() -> None:
        nonlocal current_dashboard
        if current_dashboard is not None:
            try:
                current_dashboard.will_unmount()
            except Exception:
                pass
            current_dashboard = None
        if hasattr(page, "floating_action_button"):
            page.floating_action_button = None
        if hasattr(page, "overlay"):
            page.overlay.clear()
        page.controls.clear()
        shopping_view = ShoppingView(
            page=page,
            on_back_to_dashboard=show_dashboard,
            on_open_market_mode=lambda m_name: show_market_mode(m_name),
        )
        page.add(
            ft.SafeArea(
                content=shopping_view,
                avoid_intrusions_top=True,
                avoid_intrusions_bottom=True,
                expand=True,
            )
        )
        page.update()
        shopping_view.did_mount()

    def show_market_mode(market_name: str | None = None) -> None:
        nonlocal current_dashboard
        if current_dashboard is not None:
            try:
                current_dashboard.will_unmount()
            except Exception:
                pass
            current_dashboard = None
        if hasattr(page, "floating_action_button"):
            page.floating_action_button = None
        if hasattr(page, "overlay"):
            page.overlay.clear()
        page.controls.clear()
        market_view = ShoppingMarketModeView(
            page=page,
            market_name=market_name,
            on_exit_market_mode=show_shopping,
        )
        page.add(
            ft.SafeArea(
                content=market_view,
                avoid_intrusions_top=True,
                avoid_intrusions_bottom=True,
                expand=True,
            )
        )
        page.update()
        market_view.did_mount()

    def _on_cloned_redirect(dashboard: DashboardView, target_month: str, count: int = 0) -> None:
        clean_target = target_month[:7]
        dashboard.current_month_ref = clean_target
        dashboard.month_display.value = month_label(clean_target)
        dashboard.load_data()
        msg = f"{count} despesa(s) clonada(s) para {month_label(clean_target)} com sucesso!" if count else f"Despesas clonadas para {month_label(clean_target)} com sucesso!"
        dashboard._show_snack(msg)

    def _save_session(result: dict) -> None:
        user = result.get("user", {})
        set_local_items(page, {
            "auth_token": result["token"],
            "user": user,
            "user_data": user,
            "remember_login": True,
            "remember_token": result["remember_token"],
        })

    def boot() -> None:
        # Versões anteriores guardavam a senha em texto puro: ela só é usada aqui,
        # uma única vez, para migrar ao token de "Lembrar de mim", e então é apagada.
        legacy_password = get_local_item(page, "saved_password")
        saved_email = get_local_item(page, "saved_email")
        remember_login = bool(get_local_item(page, "remember_login"))
        remember_token = get_local_item(page, "remember_token")

        try:
            # 1. Sessão de 24h ainda válida
            token = get_local_item(page, "auth_token")
            payload = verify_token(token) if token else None
            if payload:
                if remember_login and not remember_token:
                    set_local_items(page, {"remember_token": create_remember_token(
                        user_id=str(payload.get("userId", "")),
                        name=payload.get("name", ""),
                        email=payload.get("email", ""),
                    )})
                show_dashboard()
                return

            if not remember_login:
                show_auth()
                return

            # 2. "Lembrar de mim": renova a sessão pelo token de longa duração
            if remember_token:
                from services.auth_service import (
                    REMEMBER_TOKEN_INVALID,
                    REMEMBER_USER_NOT_FOUND,
                    refresh_session_with_remember_token,
                )
                success, result = refresh_session_with_remember_token(remember_token)
                if success and isinstance(result, dict):
                    _save_session(result)
                    show_dashboard()
                    return
                if result in (REMEMBER_TOKEN_INVALID, REMEMBER_USER_NOT_FOUND):
                    remove_local_item(page, "remember_token")
                else:
                    print(f"[app.py] Renovação da sessão adiada: {result}")

            # 3. Migração única de quem tinha a senha salva por versões anteriores
            elif legacy_password and saved_email:
                from services.auth_service import login_user
                success, result = login_user(email=saved_email, password=legacy_password)
                if success and isinstance(result, dict) and result.get("token"):
                    user = result.get("user", {})
                    result["remember_token"] = create_remember_token(
                        user_id=str(user.get("id", "")),
                        name=user.get("name", ""),
                        email=user.get("email", saved_email),
                    )
                    _save_session(result)
                    show_dashboard()
                    return
        except Exception as exc:
            print(f"[app.py] Auto-login falhou: {exc}")
        finally:
            if legacy_password:
                remove_local_item(page, "saved_password")

        show_auth()

    if getattr(page, "web", False) is True:
        # No modo web o Python roda no servidor: o disco não pertence ao usuário.
        # Remove qualquer cache de sessão legado e lê a sessão do navegador.
        purge_disk_cache()

        async def _boot_web() -> None:
            await preload_local_items(page, SESSION_KEYS)
            boot()

        page.run_task(_boot_web)
    else:
        boot()


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

