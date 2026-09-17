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
    ) -> None:
        super().__init__()
        self.size = size
        self.stroke_width = stroke_width
        self.ring_color = color
        self.ring_bgcolor = bgcolor

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
            color="#F1F5F9",
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
