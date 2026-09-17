"""
mai_loading.py — Componente de animação de carregamento oficial do MAI Finance.
Apresenta o logo da marca com efeito de halo pulsante e anel nas cores Teal e Rosa.
"""
from __future__ import annotations

import flet as ft


class MaiLoading(ft.Container):
    """
    Componente padrão de carregamento com a identidade visual do MAI Finance.
    Pode ser usado inline, em cartões ou como overlay de tela inteira.
    """

    def __init__(
        self,
        message: str = "Carregando...",
        size: float = 48,
        theme_mode: str = "dark",
        is_card: bool = False,
    ):
        is_light = theme_mode == "light"
        text_color = "#334155" if is_light else "#EDF0F7"
        subtext_color = "#64748B" if is_light else "#8891A8"
        bg_card = "#FFFFFF" if is_light else "#151B2E"
        border_card = "#E2E8F0" if is_light else "#232A45"

        # Logo central da marca
        logo_img = ft.Image(
            src="logo.png",
            width=size,
            height=size,
            fit=ft.BoxFit.CONTAIN,
        )

        # Anel de progresso sutil com a cor Teal oficial circulando o logo
        ring = ft.ProgressRing(
            width=size + 24,
            height=size + 24,
            stroke_width=3,
            color="#3FD6C4",
            bgcolor="rgba(63, 214, 196, 0.15)",
        )

        logo_stack = ft.Stack(
            controls=[
                # Anel externo giratório
                ft.Container(
                    content=ring,
                    alignment=ft.Alignment.CENTER,
                    width=size + 28,
                    height=size + 28,
                ),
                # Halo pulsante de fundo
                ft.Container(
                    width=size + 10,
                    height=size + 10,
                    border_radius=999,
                    bgcolor="rgba(63, 214, 196, 0.08)",
                    alignment=ft.Alignment.CENTER,
                ),
                # Logo no centro absoluto
                ft.Container(
                    content=logo_img,
                    alignment=ft.Alignment.CENTER,
                    width=size + 28,
                    height=size + 28,
                ),
            ],
            width=size + 28,
            height=size + 28,
            alignment=ft.Alignment.CENTER,
        )

        items: list[ft.Control] = [logo_stack]

        if message:
            items.append(
                ft.Text(
                    message,
                    size=13,
                    weight=ft.FontWeight.W_500,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        content_col = ft.Column(
            controls=items,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=14,
            tight=True,
        )

        super().__init__(
            content=content_col,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.all(24) if is_card else ft.Padding.all(12),
            bgcolor=bg_card if is_card else None,
            border=ft.Border.all(1, border_card) if is_card else None,
            border_radius=16 if is_card else None,
        )

    @classmethod
    def full_screen_overlay(
        cls,
        message: str = "Processando...",
        theme_mode: str = "dark",
    ) -> ft.Container:
        """Cria um overlay semitransparente bloqueante para ações globais (login, sync)."""
        is_light = theme_mode == "light"
        overlay_bg = "rgba(234, 237, 246, 0.85)" if is_light else "rgba(8, 9, 15, 0.88)"
        return ft.Container(
            content=cls(message=message, size=52, theme_mode=theme_mode, is_card=True),
            alignment=ft.Alignment.CENTER,
            bgcolor=overlay_bg,
            expand=True,
        )

    @classmethod
    def button_spinner(cls, label: str = "Salvando...") -> ft.Row:
        """Cria indicador ultracompacto para botões com ação em andamento."""
        return ft.Row(
            controls=[
                ft.ProgressRing(width=16, height=16, stroke_width=2.5, color="#08090F"),
                ft.Text(label, weight=ft.FontWeight.BOLD, size=13, color="#08090F"),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
