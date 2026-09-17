"""
theme.py — Tokens de design system, cores e utilitários de formatação do MAI Finance.

Paridade com lib/theme.ts:
- Modos escuro (dark) e claro (light)
- Cores de categorias padrão
- Funções de formatação BRL e manipulação de month_ref
"""
from __future__ import annotations

import calendar
from datetime import datetime

CATEGORIES = [
    {"id": "outros", "name": "Outros", "dark": "#94A3B8", "light": "#475569", "color": "#94A3B8"},
    {"id": "daae", "name": "DAAE", "dark": "#5EA8F2", "light": "#1D4ED8", "color": "#5EA8F2"},
    {"id": "condinvest", "name": "CondInvest", "dark": "#B399F5", "light": "#7C3AED", "color": "#B399F5"},
    {"id": "imposto", "name": "Imposto", "dark": "#F5738C", "light": "#BE123C", "color": "#F5738C"},
    {"id": "caixa", "name": "Caixa", "dark": "#F2B84B", "light": "#B45309", "color": "#F2B84B"},
    {"id": "cpfl", "name": "CPFL", "dark": "#3FD6C4", "light": "#0F766E", "color": "#3FD6C4"},
]

MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

MONTH_ABBRS = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "pageBg": "#08090F",
        "surface": "#121628",
        "surfaceSolid": "#151B2E",
        "surfaceGradientA": "#151B32",
        "surfaceGradientB": "#111525",
        "border": "#232A45",
        "borderSubtle": "#1B2138",
        "textPrimary": "#EDF0F7",
        "textMuted": "#8891A8",
        "textFaint": "#606A85",
        "rowHover": "#161C34",
        "accent": "#3FD6C4",
        "accentTo": "#5B7FF5",
        "accentOnBrand": "#08090F",
        "success": "#3FD6C4",
        "successText": "#5EE0C4",
        "successBg": "#122620",
        "successBorder": "#1F3D33",
        "warning": "#F2B84B",
        "warningBg": "#241D0F",
        "warningBorder": "#3D3320",
        "danger": "#F5738C",
        "inputBg": "#0A0D18",
        "ring1": "#3FD6C4",
        "ring2": "#5EE0C4",
        "ringTrack": "#1E2540",
    },
    "light": {
        "pageBg": "#EAEDF6",
        "surface": "#FFFFFF",
        "surfaceSolid": "#FFFFFF",
        "surfaceGradientA": "#FFFFFF",
        "surfaceGradientB": "#F6F8FC",
        "border": "#E1E5F0",
        "borderSubtle": "#EAEDF5",
        "textPrimary": "#131826",
        "textMuted": "#5B6478",
        "textFaint": "#8890A3",
        "rowHover": "#F4F6FC",
        "accent": "#0E9488",
        "accentTo": "#3B5FE0",
        "accentOnBrand": "#FFFFFF",
        "success": "#0D9488",
        "successText": "#0D9488",
        "successBg": "#ECFBF8",
        "successBorder": "#CBEFE8",
        "warning": "#B45309",
        "warningBg": "#FFF7EB",
        "warningBorder": "#F5E3C4",
        "danger": "#BE123C",
        "inputBg": "#FFFFFF",
        "ring1": "#0D9488",
        "ring2": "#3FD6C4",
        "ringTrack": "#E4E8F0",
    },
}


def get_tokens(theme_mode: str = "dark") -> dict[str, str]:
    """Retorna o dicionário de tokens para o modo informado."""
    return THEMES.get(theme_mode, THEMES["dark"])


def format_brl(value: float | int | None) -> str:
    """Formata valor numérico para padrão BRL (ex.: R$ 1.234,56)."""
    if value is None:
        value = 0.0
    val = float(value)
    formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def month_label(month_ref: str) -> str:
    """Converte 'AAAA-MM' para 'Mês AAAA' (ex: '2026-09' -> 'Setembro 2026')."""
    try:
        parts = month_ref[:7].split("-")
        y = int(parts[0])
        m = int(parts[1])
        if 1 <= m <= 12:
            return f"{MONTH_NAMES[m - 1]} {y}"
    except Exception:
        pass
    return month_ref


def shift_month(month_ref: str, delta: int) -> str:
    """Desloca o mês por delta positivo ou negativo."""
    try:
        parts = month_ref[:7].split("-")
        y = int(parts[0])
        m = int(parts[1])
        total_m = y * 12 + (m - 1) + delta
        new_y = total_m // 12
        new_m = (total_m % 12) + 1
        return f"{new_y:04d}-{new_m:02d}"
    except Exception:
        return month_ref


def get_current_month_ref() -> str:
    """Retorna o mês atual no formato AAAA-MM."""
    return datetime.now().strftime("%Y-%m")


def get_max_days_in_month(month_ref: str) -> int:
    """Retorna o total de dias do mês especificado."""
    try:
        parts = month_ref[:7].split("-")
        y = int(parts[0])
        m = int(parts[1])
        return calendar.monthrange(y, m)[1]
    except Exception:
        return 31


def format_payment_date_to_ui(date_str: str | None) -> str:
    """Formata data ISO AAAA-MM-DD para 'D.mmm' (ex: 2026-09-15 -> 15.set)."""
    if not date_str:
        return ""
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            d = int(parts[2])
            m = int(parts[1])
            if 1 <= m <= 12:
                return f"{d}.{MONTH_ABBRS[m - 1]}"
    except Exception:
        pass
    return date_str
