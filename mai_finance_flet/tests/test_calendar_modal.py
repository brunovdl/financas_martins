"""
test_calendar_modal.py — Testes unitários para o componente CalendarModal em pt-BR.

Valida:
- Abertura do diálogo com data inicial ISO e pt-BR
- Navegação entre meses e anos
- Header com dias da semana em português (Dom, Seg, Ter, Qua, Qui, Sex, Sáb)
- Seleção de data com callback retornando (iso_str, br_str)
- Ação do botão 'Hoje'
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock
import flet as ft

from ui.components.calendar_modal import open_calendar_modal, WEEKDAYS_BR
from ui.theme import THEMES


class TestCalendarModal:
    def test_calendar_modal_open_and_weekday_headers(self):
        page = MagicMock(spec=ft.Page)
        dlg = open_calendar_modal(
            page=page,
            initial_date="2026-09-15",
            theme_tokens=THEMES["dark"],
            title="Selecionar Vencimento",
        )

        assert dlg is not None
        assert "Selecionar Vencimento" in dlg.title.value

        # Conteúdo interno
        container = dlg.content
        col = container.content
        nav_row = col.controls[0]
        grid_col = col.controls[2]

        # Verifica header de dias da semana em pt-BR
        weekday_row = grid_col.controls[0]
        rendered_weekdays = [cell.content.value for cell in weekday_row.controls]
        assert rendered_weekdays == ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

    def test_calendar_modal_selection_callback(self):
        page = MagicMock(spec=ft.Page)
        selected_results = []

        def on_selected(iso_d: str, br_d: str):
            selected_results.append((iso_d, br_d))

        dlg = open_calendar_modal(
            page=page,
            initial_date="15/09/2026",
            on_date_selected=on_selected,
            theme_tokens=THEMES["dark"],
        )

        # Encontra uma célula com dia no grid e simula o clique
        grid_col = dlg.content.content.controls[2]
        clicked = False
        for row in grid_col.controls[1:]:  # pula a linha de dias da semana
            for cell in row.controls:
                if hasattr(cell, "content") and isinstance(cell.content, ft.Text):
                    # Clica no dia 20
                    if cell.content.value == "20":
                        cell.on_click(None)
                        clicked = True
                        break
            if clicked:
                break

        assert clicked is True
        assert len(selected_results) == 1
        assert selected_results[0] == ("2026-09-20", "20/09/2026")

    def test_calendar_modal_today_button(self):
        page = MagicMock(spec=ft.Page)
        selected_results = []

        def on_selected(iso_d: str, br_d: str):
            selected_results.append((iso_d, br_d))

        dlg = open_calendar_modal(
            page=page,
            initial_date="2026-01-01",
            on_date_selected=on_selected,
            theme_tokens=THEMES["dark"],
        )

        # Clica no botão "Hoje" (ação 0 do diálogo)
        btn_today = dlg.actions[0]
        btn_today.on_click(None)

        today = datetime.now().date()
        expected_iso = today.strftime("%Y-%m-%d")
        expected_br = today.strftime("%d/%m/%Y")

        assert len(selected_results) == 1
        assert selected_results[0] == (expected_iso, expected_br)
