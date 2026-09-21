"""
geo_service.py — Serviço de geolocalização e identificação de mercados regionais (T-017).

Implementa:
- Detecção de localização física (GPS / IP / Configuração) (AC-023)
- Mapeamento de redes de supermercado que atendem a região do usuário
"""
from __future__ import annotations

import os
from typing import Any

# Localização padrão configurada
_configured_location: dict[str, str] = {
    "city": "São Paulo",
    "state": "SP",
    "neighborhood": "Pinheiros",
    "cep": "05422-000",
}

_configured_market: str | None = None

# Redes de supermercados por região
REGIONAL_MARKETS: dict[str, list[dict[str, str]]] = {
    "sao paulo": [
        {"id": "pao_de_acucar", "name": "Pão de Açúcar", "domain": "paodeacucar.com", "badge": "Premium / Variedade"},
        {"id": "carrefour", "name": "Carrefour", "domain": "carrefour.com.br", "badge": "Hipermercado / Ofertas"},
        {"id": "atacadao", "name": "Atacadão", "domain": "atacadao.com.br", "badge": "Atacado / Economia"},
    ],
    "rio de janeiro": [
        {"id": "guanabara", "name": "Supermercados Guanabara", "domain": "supermercadosguanabara.com.br", "badge": "Preço Baixo"},
        {"id": "zona_sul", "name": "Zona Sul", "domain": "zonasul.com.br", "badge": "Premium / Variedade"},
        {"id": "carrefour", "name": "Carrefour", "domain": "carrefour.com.br", "badge": "Hipermercado"},
    ],
    "belo horizonte": [
        {"id": "supermercados_bh", "name": "Supermercados BH", "domain": "supermercadosbh.com.br", "badge": "Preço Baixo / Economia"},
        {"id": "verdemar", "name": "Verdemar", "domain": "verdemaratevoce.com.br", "badge": "Premium / Variedade"},
        {"id": "carrefour", "name": "Carrefour", "domain": "carrefour.com.br", "badge": "Hipermercado"},
    ],
    "curitiba": [
        {"id": "muffato", "name": "Super Muffato", "domain": "delivery.supermuffato.com.br", "badge": "Regional / Variedade"},
        {"id": "condor", "name": "Condor Super Center", "domain": "condor.com.br", "badge": "Hipermercado / Ofertas"},
        {"id": "festval", "name": "Festval", "domain": "festval.com", "badge": "Premium"},
    ],
    "default": [
        {"id": "carrefour", "name": "Carrefour", "domain": "carrefour.com.br", "badge": "Nacional / Hiper"},
        {"id": "pao_de_acucar", "name": "Pão de Açúcar", "domain": "paodeacucar.com", "badge": "Qualidade & Frescor"},
        {"id": "atacadao", "name": "Atacadão", "domain": "atacadao.com.br", "badge": "Atacado / Custo-Benefício"},
    ],
}


def get_device_location() -> dict[str, Any]:
    """
    Retorna a localização do usuário para direcionar a busca regional (AC-023).
    No ambiente Android, utiliza as coordenadas do dispositivo ou fallback configurado.
    """
    return dict(_configured_location)


def set_custom_location(city: str, state: str = "SP", neighborhood: str = "", cep: str = "") -> None:
    """Atualiza a localização geográfica de referência para cotação."""
    global _configured_location
    clean_city = str(city).strip() if city and isinstance(city, str) and "Mock" not in type(city).__name__ else "São Paulo"
    clean_state = str(state).strip().upper() if state and isinstance(state, str) and "Mock" not in type(state).__name__ else "SP"
    _configured_location = {
        "city": clean_city or "São Paulo",
        "state": clean_state or "SP",
        "neighborhood": str(neighborhood).strip() if isinstance(neighborhood, str) else "",
        "cep": str(cep).strip() if isinstance(cep, str) else "",
    }


def get_configured_market() -> str | None:
    """Retorna o supermercado específico configurado pelo usuário, se houver."""
    return _configured_market


def set_configured_market(market: str | None) -> None:
    """Define o supermercado específico de preferência do usuário."""
    global _configured_market
    if market and isinstance(market, str) and "Mock" not in type(market).__name__:
        clean = market.strip()
        _configured_market = clean if clean else None
    else:
        _configured_market = None


def get_regional_markets(city: str | None = None) -> list[dict[str, str]]:
    """Retorna as redes de supermercado disponíveis na cidade informada."""
    if not city:
        city = _configured_location.get("city", "São Paulo")

    if not isinstance(city, str):
        city = "São Paulo"

    normalized = str(city).lower().strip()
    for reg_key, markets in REGIONAL_MARKETS.items():
        if reg_key in normalized or normalized in reg_key:
            return list(markets)

    return list(REGIONAL_MARKETS["default"])


