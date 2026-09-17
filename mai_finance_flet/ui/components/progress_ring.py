"""
progress_ring.py — Componente visual reutilizável de anel de progresso financeiro.

Exibe anel circular proporcional ao percentual de despesas pagas vs total
com rótulo numérico centralizado e cores do Design System MAI Finance.
"""
from __future__ import annotations

import flet as ft


class FinancialProgressRing(ft.Container):
    """Anel de progresso financeiro (AC-007)."""

    def __init__(
        self,
        pct: float = 0.0,
        size: int = 72,
        stroke_width: int = 6,
        color: str = "#3FD6C4",
        bgcolor: str = "#1E293B",
        text_color: str = "#F1F5F9",
    ) -> None:
        super().__init__()
        self.size = size
        self.stroke_width = stroke_width
        self.ring_color = color
        self.ring_bgcolor = bgcolor
        self.text_color = text_color

        # Normaliza pct entre 0.0 e 100.0
        normalized_pct = max(0.0, min(100.0, float(pct)))
        self.ring = ft.ProgressRing(
            value=normalized_pct / 100.0,
            stroke_width=self.stroke_width,
            color=self.ring_color,
            bgcolor=self.ring_bgcolor,
            width=self.size,
            height=self.size,
        )

        self.label = ft.Text(
            f"{int(round(normalized_pct))}%",
            size=max(11, int(self.size * 0.2)),
            weight=ft.FontWeight.BOLD,
            color=self.text_color,
            text_align=ft.TextAlign.CENTER,
        )

        self.content = ft.Stack(
            [
                self.ring,
                ft.Container(
                    content=self.label,
                    alignment=ft.Alignment.CENTER,
                    width=self.size,
                    height=self.size,
                ),
            ],
            alignment=ft.Alignment.CENTER,
            width=self.size,
            height=self.size,
        )
        self.width = self.size
        self.height = self.size
        self.alignment = ft.Alignment.CENTER

    def set_pct(self, pct: float) -> None:
        """Atualiza dinamicamente a porcentagem do anel."""
        normalized = max(0.0, min(100.0, float(pct)))
        self.ring.value = normalized / 100.0
        self.label.value = f"{int(round(normalized))}%"

    def apply_theme(
        self,
        tokens: dict[str, str] | None = None,
        *,
        text_color: str | None = None,
        track_color: str | None = None,
        ring_color: str | None = None,
    ) -> None:
        """Atualiza dinamicamente as cores do anel, trilha e texto com suporte a tokens de tema."""
        if isinstance(tokens, dict):
            self.label.color = tokens.get("textPrimary", "#F1F5F9")
            self.ring_bgcolor = tokens.get("ringTrack", tokens.get("borderSubtle", "#1E293B"))
            self.ring.bgcolor = self.ring_bgcolor
            self.ring_color = tokens.get("ring1", tokens.get("success", "#3FD6C4"))
            self.ring.color = self.ring_color
        if text_color:
            self.label.color = text_color
        if track_color:
            self.ring_bgcolor = track_color
            self.ring.bgcolor = track_color
        if ring_color:
            self.ring_color = ring_color
            self.ring.color = ring_color
