"""
auth_view.py — Tela de Autenticação (Login e Cadastro) do MAI Finance.

Paridade visual com AuthPage.tsx e Design System MAI Finance:
- Dark theme com tons #151B2E, #0B1120 e destaque #3FD6C4
- Alternância entre abas 'Entrar' e 'Criar Conta'
- Validações inline com feedback em tempo real
- Medidor dinâmico de força de senha
- Submissão com tecla ENTER em todos os campos de entrada
- Opção para salvar e lembrar e-mail e senha no dispositivo
- Alvos de toque otimizados (mínimo 48px)
- Salva token e dados do usuário com persistência garantida
"""
from __future__ import annotations

from typing import Callable
import flet as ft

from services.auth_service import login_user, register_user
from ui.storage_util import get_local_item, set_local_item, set_local_items, remove_local_item
from ui.components.mai_loading import MaiLoading


class AuthView(ft.Container):
    """Componente de tela cheia para Login e Cadastro."""

    def __init__(
        self,
        page: ft.Page,
        on_login_success: Callable[[str, dict], None] | None = None,
    ) -> None:
        super().__init__()
        self.page_ref = page
        self.on_login_success = on_login_success
        self.current_tab = "login"  # 'login' ou 'register'

        self.expand = True
        self.bgcolor = "#0B1120"
        self.alignment = ft.Alignment.CENTER
        self.padding = 20

        # Carrega credenciais salvas do armazenamento local / disco
        saved_email = get_local_item(page, "saved_email") or ""
        saved_password = get_local_item(page, "saved_password") or ""
        remember_login = get_local_item(page, "remember_login")
        if remember_login is None:
            remember_login = True

        # Borda moderna compatível com Flet 1.0
        input_border = {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(border_radius=12, side=ft.BorderSide(1, "#334155")),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(border_radius=12, side=ft.BorderSide(1, "#3FD6C4")),
        }

        # Controles de formulário com submissão por ENTER
        self.name_field = ft.TextField(
            label="Nome de usuário",
            hint_text="Seu nome ou apelido",
            prefix_icon=ft.Icons.PERSON,
            bgcolor="#151B2E",
            border=input_border,
            color="#F1F5F9",
            visible=False,
            height=56,
            on_submit=self._on_name_submit,
        )

        self.email_field = ft.TextField(
            label="Endereço de E-mail",
            value=saved_email,
            hint_text="seu.email@exemplo.com",
            keyboard_type=ft.KeyboardType.EMAIL,
            prefix_icon=ft.Icons.EMAIL,
            bgcolor="#151B2E",
            border=input_border,
            color="#F1F5F9",
            height=56,
            on_submit=self._on_email_submit,
        )

        self.password_field = ft.TextField(
            label="Senha (Mínimo 8 caracteres)",
            value=saved_password,
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            bgcolor="#151B2E",
            border=input_border,
            color="#F1F5F9",
            height=56,
            on_change=self._on_password_change,
            on_submit=self._handle_submit,
        )

        # Checkbox para salvar e-mail e senha
        self.remember_checkbox = ft.Checkbox(
            label="Lembrar e-mail e senha neste dispositivo",
            value=bool(remember_login),
            check_color="#08090F",
            active_color="#3FD6C4",
            label_style=ft.TextStyle(size=12, color="#94A3B8"),
        )

        # Medidor de força de senha
        self.strength_label = ft.Text(
            "Requisito: 0/8 caracteres",
            size=11,
            color="#94A3B8",
        )
        self.strength_bar = ft.ProgressBar(
            value=0.0,
            color="#F2B84B",
            bgcolor="#1E293B",
            bar_height=4,
            border_radius=2,
        )
        self.strength_container = ft.Column(
            [self.strength_label, self.strength_bar],
            spacing=4,
            visible=False,
        )

        # Caixa de alerta de erro
        self.error_text = ft.Text("", size=13, color="#F5738C", expand=True)
        self.error_box = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color="#F5738C", size=20),
                    self.error_text,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor="#2D151D",
            border=ft.Border.all(1, "#83243A"),
            border_radius=12,
            padding=12,
            visible=False,
        )

        # Botão de submissão
        self.submit_spinner = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2.5,
            color="#0B1120",
            visible=False,
        )
        self.submit_btn_text = ft.Text(
            "Acessar Conta",
            size=15,
            weight=ft.FontWeight.BOLD,
            color="#0B1120",
        )
        self.submit_btn_icon = ft.Icon(
            ft.Icons.ARROW_FORWARD,
            size=18,
            color="#0B1120",
        )
        self.submit_button = ft.Button(
            content=ft.Row(
                [self.submit_spinner, self.submit_btn_text, self.submit_btn_icon],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "#3FD6C4",
                    ft.ControlState.HOVERED: "#2EC4B2",
                    ft.ControlState.DISABLED: "#1E293B",
                },
                color={
                    ft.ControlState.DEFAULT: "#0B1120",
                    ft.ControlState.DISABLED: "#64748B",
                },
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.symmetric(vertical=16, horizontal=24),
            ),
            height=52,
            on_click=self._handle_submit,
        )

        # Abas 'Entrar' e 'Criar Conta'
        self.tab_login_btn = ft.Container(
            content=ft.Text(
                "Entrar",
                size=14,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            bgcolor="#3FD6C4",
            border_radius=10,
            padding=ft.Padding.symmetric(vertical=10),
            expand=True,
            on_click=lambda _: self._switch_tab("login"),
            ink=True,
        )
        self.tab_register_btn = ft.Container(
            content=ft.Text(
                "Criar Conta",
                size=14,
                weight=ft.FontWeight.W_500,
                color="#94A3B8",
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            bgcolor=None,
            border_radius=10,
            padding=ft.Padding.symmetric(vertical=10),
            expand=True,
            on_click=lambda _: self._switch_tab("register"),
            ink=True,
        )

        tab_selector = ft.Container(
            content=ft.Row(
                [self.tab_login_btn, self.tab_register_btn],
                spacing=4,
            ),
            bgcolor="#151B2E",
            border=ft.Border.all(1, "#1E293B"),
            border_radius=12,
            padding=4,
        )

        # Card Principal de Autenticação
        card_content = ft.Column(
            [
                # Header com Logo Oficial da Marca MAI Finance
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Image(
                                src="logo.png",
                                width=56,
                                height=56,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            alignment=ft.Alignment.CENTER,
                            padding=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(
                            "MAI Finance",
                            size=26,
                            weight=ft.FontWeight.BOLD,
                            color="#F1F5F9",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Gestão Financeira Inteligente & Protegida",
                            size=13,
                            color="#94A3B8",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                ft.Divider(color="transparent", height=6),
                tab_selector,
                self.error_box,
                self.name_field,
                self.email_field,
                self.password_field,
                self.remember_checkbox,
                self.strength_container,
                ft.Divider(color="transparent", height=4),
                self.submit_button,
                ft.Divider(color="#1E293B", height=16),
                # Rodapé de segurança 24h
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ACCESS_TIME, size=14, color="#3FD6C4"),
                                ft.Text("Sessão por 24 horas", size=12, color="#94A3B8"),
                            ],
                            spacing=4,
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.SHIELD, size=14, color="#3FD6C4"),
                                ft.Text("JWT Protegido", size=12, color="#64748B"),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        page_w = 800.0
        try:
            raw_w = getattr(self.page_ref, "width", None)
            if isinstance(raw_w, (int, float)):
                page_w = float(raw_w)
        except Exception:
            page_w = 800.0

        card_w = min(page_w - 32, 420)
        is_narrow = page_w < 450

        self.content = ft.Container(
            content=ft.Column(
                [card_content],
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=card_w,
            bgcolor="#151B2E",
            border=ft.Border.all(1, "#1E293B"),
            border_radius=20,
            padding=ft.Padding.symmetric(
                horizontal=20 if is_narrow else 32,
                vertical=24 if is_narrow else 32,
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=24,
                color="#00000088",
            ),
        )

        if saved_password:
            self._update_password_meter(saved_password)

    def _on_email_submit(self, _: ft.ControlEvent | None = None) -> None:
        """Pressionar Enter no e-mail foca na senha se vazia, ou submete."""
        if not (self.password_field.value or "").strip():
            self.password_field.focus()
        else:
            self._handle_submit(None)

    def _on_name_submit(self, _: ft.ControlEvent | None = None) -> None:
        """Pressionar Enter no nome foca no e-mail."""
        self.email_field.focus()

    def _switch_tab(self, tab: str) -> None:
        """Alterna entre as abas 'login' e 'register'."""
        self.current_tab = tab
        self._clear_error()

        is_login = tab == "login"
        self.name_field.visible = not is_login
        self.remember_checkbox.visible = is_login
        self.tab_login_btn.bgcolor = "#3FD6C4" if is_login else None
        self.tab_login_btn.content.color = "#0B1120" if is_login else "#94A3B8"
        self.tab_login_btn.content.weight = ft.FontWeight.BOLD if is_login else ft.FontWeight.W_500

        self.tab_register_btn.bgcolor = "#3FD6C4" if not is_login else None
        self.tab_register_btn.content.color = "#0B1120" if not is_login else "#94A3B8"
        self.tab_register_btn.content.weight = ft.FontWeight.BOLD if not is_login else ft.FontWeight.W_500

        self.submit_btn_text.value = "Acessar Conta" if is_login else "Concluir Cadastro"
        self.page_ref.update()

    def _update_password_meter(self, val: str) -> None:
        length = len(val)
        if length == 0:
            self.strength_container.visible = False
        else:
            self.strength_container.visible = True
            if length < 8:
                self.strength_label.value = f"Requisito: {length}/8 caracteres"
                self.strength_label.color = "#F2B84B"
                self.strength_bar.value = min(length / 8.0, 0.5)
                self.strength_bar.color = "#F2B84B"
            elif length < 12:
                self.strength_label.value = f"Senha segura ({length}/8)"
                self.strength_label.color = "#3FD6C4"
                self.strength_bar.value = 0.75
                self.strength_bar.color = "#3FD6C4"
            else:
                self.strength_label.value = f"Senha excelente ({length}/8)"
                self.strength_label.color = "#10B981"
                self.strength_bar.value = 1.0
                self.strength_bar.color = "#10B981"

    def _on_password_change(self, _: ft.ControlEvent) -> None:
        """Atualiza a barra de força e requisitos de senha em tempo real."""
        val = self.password_field.value or ""
        self._update_password_meter(val)
        self.page_ref.update()

    def _show_error(self, message: str) -> None:
        """Exibe mensagem de erro na caixa de alerta."""
        self.error_text.value = message
        self.error_box.visible = True
        self._set_loading(False)
        self.page_ref.update()

    def _clear_error(self) -> None:
        """Limpa e esconde mensagem de erro."""
        self.error_text.value = ""
        self.error_box.visible = False

    def _set_loading(self, loading: bool) -> None:
        """Alterna estado de carregamento do botão submit."""
        self.submit_spinner.visible = loading
        self.submit_btn_icon.visible = not loading
        self.submit_button.disabled = loading
        self.page_ref.update()

    def _handle_submit(self, _: ft.ControlEvent | None = None) -> None:
        """Validação inline e envio de login/registro."""
        self._clear_error()

        email = (self.email_field.value or "").strip()
        password = self.password_field.value or ""
        name = (self.name_field.value or "").strip()

        # Validações locais inline
        if not email or "@" not in email or "." not in email:
            self._show_error("Por favor, informe um e-mail válido.")
            return

        if len(password) < 8:
            self._show_error("A senha deve conter no mínimo 8 caracteres.")
            return

        if self.current_tab == "register" and not name:
            self._show_error("Por favor, insira o seu nome de usuário.")
            return

        self._set_loading(True)

        try:
            if self.current_tab == "login":
                print(f"[AuthView] Tentando login para: {email}")
                success, result = login_user(email=email, password=password)
            else:
                print(f"[AuthView] Tentando cadastro para: {email}")
                success, result = register_user(name=name, email=email, password=password)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"[AuthView] Erro inesperado na chamada de autenticação: {exc}")
            self._show_error(f"Erro de comunicação: {exc}")
            return

        if not success:
            print(f"[AuthView] Falha na autenticação: {result}")
            self._show_error(str(result))
            return

        print(f"[AuthView] Autenticação bem-sucedida para: {email}")

        # Login/Registro bem-sucedido
        data = result if isinstance(result, dict) else {}
        token = data.get("token", "")
        user = data.get("user", {})

        # Salva credenciais e dados de sessão em lote (uma única gravação atômica)
        batch_items: dict[str, Any] = {
            "auth_token": token,
            "user": user,
            "user_data": user,
            "remember_login": bool(self.remember_checkbox.value),
        }
        if self.remember_checkbox.value:
            batch_items["saved_email"] = email
            batch_items["saved_password"] = password
        else:
            remove_local_item(self.page_ref, "saved_email")
            remove_local_item(self.page_ref, "saved_password")

        set_local_items(self.page_ref, batch_items)

        # Transição direta para a Dashboard (não chama _set_loading(False) para evitar conflito de update no WebSocket)
        if self.on_login_success:
            self.on_login_success(token, user)
