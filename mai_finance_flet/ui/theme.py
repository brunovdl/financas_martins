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
        "tableHeaderBg": "#151B2E",
        "tableHeaderBorder": "#232A45",
        "textPrimary": "#EDF0F7",
        "textHeader": "#EDF0F7",
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
        "surfaceGradientB": "#F8FAFC",
        "border": "#CBD5E1",
        "borderSubtle": "#E2E8F0",
        "tableHeaderBg": "#F1F5F9",
        "tableHeaderBorder": "#CBD5E1",
        "textPrimary": "#0F172A",
        "textHeader": "#1E293B",
        "textMuted": "#334155",
        "textFaint": "#64748B",
        "rowHover": "#F8FAFC",
        "accent": "#0E9488",
        "accentTo": "#3B5FE0",
        "accentOnBrand": "#FFFFFF",
        "success": "#0E9488",
        "successText": "#0E9488",
        "successBg": "#ECFDF5",
        "successBorder": "#A7F3D0",
        "warning": "#B45309",
        "warningBg": "#FFFBEB",
        "warningBorder": "#FDE68A",
        "danger": "#BE123C",
        "inputBg": "#FFFFFF",
        "ring1": "#0D9488",
        "ring2": "#3FD6C4",
        "ringTrack": "#E2E8F0",
    },
}


def get_tokens(theme_mode: str = "dark") -> dict[str, str]:
    """Retorna o dicionário de tokens para o modo informado."""
    return THEMES.get(theme_mode, THEMES["dark"])


def get_badge_colors(color_hex: str | None, is_light: bool = False) -> tuple[str, str, str]:
    """
    Calcula (bgcolor, text_color, border_color) com contraste garantido.
    No tema claro: fundo suave pastel (15-20% opacidade), texto escuro e saturado.
    No tema escuro: fundo sólido vibrante ou semi-transparente com texto branco nítido.
    """
    raw = (color_hex or "#94A3B8").strip()
    if not raw.startswith("#"):
        raw = f"#{raw}"

    # Fallback caso a cor seja inválida
    if len(raw) not in (4, 7):
        raw = "#94A3B8"

    if len(raw) == 4:
        raw = f"#{raw[1]*2}{raw[2]*2}{raw[3]*2}"

    try:
        r = int(raw[1:3], 16)
        g = int(raw[3:5], 16)
        b = int(raw[5:7], 16)
    except Exception:
        r, g, b = 148, 163, 184

    if is_light:
        # Fundo suave pastel
        bg = f"rgba({r}, {g}, {b}, 0.16)"
        border = f"rgba({r}, {g}, {b}, 0.40)"
        # Escurece a cor em 50% para texto de alto contraste no tema claro
        dr = max(0, int(r * 0.45))
        dg = max(0, int(g * 0.45))
        db = max(0, int(b * 0.45))
        text = f"#{dr:02x}{dg:02x}{db:02x}"
        return bg, text, border
    else:
        # No tema escuro: fundo escurecido sutil com texto brilhante
        bg = f"rgba({r}, {g}, {b}, 0.22)"
        border = f"rgba({r}, {g}, {b}, 0.50)"
        # Clareia ou mantém vibrante
        text = f"#{min(255, int(r * 1.15)):02x}{min(255, int(g * 1.15)):02x}{min(255, int(b * 1.15)):02x}"
        return bg, text, border


HIDDEN_CURRENCY_MASK = "R$ •••••"


def format_brl(value: float | int | None, hide_values: bool = False) -> str:
    """Formata valor numérico para padrão BRL (ex.: R$ 1.234,56). Se hide_values=True, retorna HIDDEN_CURRENCY_MASK."""
    if hide_values:
        return HIDDEN_CURRENCY_MASK
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


def iso_to_br_date(iso_date: str | None) -> str:
    """Converte data ISO (AAAA-MM-DD) para pt-BR (DD/MM/AAAA)."""
    if not iso_date:
        return ""
    iso_date = str(iso_date).strip()
    if "/" in iso_date and len(iso_date.split("/")) == 3:
        return iso_date
    try:
        parts = iso_date.split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{d:02d}/{m:02d}/{y:04d}"
    except Exception:
        pass
    return iso_date


def br_to_iso_date(br_date: str | None) -> str:
    """Converte data pt-BR (DD/MM/AAAA ou DD-MM-AAAA) para ISO (AAAA-MM-DD)."""
    if not br_date:
        return ""
    br_date = str(br_date).strip()
    sep = "/" if "/" in br_date else ("-" if "-" in br_date else None)
    if sep:
        parts = br_date.split(sep)
        if len(parts) == 3:
            if len(parts[0]) <= 2 and len(parts[2]) == 4:
                try:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    return f"{y:04d}-{m:02d}-{d:02d}"
                except Exception:
                    pass
            elif len(parts[0]) == 4 and len(parts[2]) <= 2:
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    return f"{y:04d}-{m:02d}-{d:02d}"
                except Exception:
                    pass
    return br_date


def format_payment_date_to_ui(date_str: str | None) -> str:
    """Formata data ISO AAAA-MM-DD para 'DD/MM/AAAA' (ex: 2026-09-15 -> 15/09/2026)."""
    return iso_to_br_date(date_str)
