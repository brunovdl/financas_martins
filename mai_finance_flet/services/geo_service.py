"""
geo_service.py — Serviço de geolocalização e identificação de mercados regionais (T-017).

Implementa:
- Detecção de localização física nativa via GPS (flet-geolocator, DEC-029) com reverse geocoding
- Fallback resiliente multi-provedor por GeoIP (ip-api.com, ipwho.is, ipapi.co)
- Mapeamento de redes de supermercado que atendem a região do usuário
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

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
    "campinas": [
        {"id": "enxuto", "name": "Enxuto Supermercados", "domain": "enxuto.com.br", "badge": "Regional / Variedade"},
        {"id": "savegnago", "name": "Savegnago", "domain": "savegnago.com.br", "badge": "Líder Regional"},
        {"id": "dalben", "name": "Dalben Supermercados", "domain": "dalben.com.br", "badge": "Gourmet / Frescor"},
    ],
    "ribeirao preto": [
        {"id": "savegnago", "name": "Savegnago", "domain": "savegnago.com.br", "badge": "Líder Regional"},
        {"id": "mialich", "name": "Mialich Supermercados", "domain": "mialich.com.br", "badge": "Preço Baixo"},
        {"id": "carrefour", "name": "Carrefour", "domain": "carrefour.com.br", "badge": "Hipermercado"},
    ],
    "santos": [
        {"id": "pao_de_acucar", "name": "Pão de Açúcar", "domain": "paodeacucar.com", "badge": "Variedade"},
        {"id": "litoral_hiper", "name": "Litoral Hipermercados", "domain": "litoralhiper.com.br", "badge": "Regional"},
        {"id": "atacadao", "name": "Atacadão", "domain": "atacadao.com.br", "badge": "Atacado"},
    ],
    "sao jose dos campos": [
        {"id": "shibata", "name": "Shibata Supermercados", "domain": "shibata.com.br", "badge": "Líder Regional"},
        {"id": "tauste", "name": "Tauste Supermercados", "domain": "tauste.com.br", "badge": "Variedade / Ofertas"},
        {"id": "spani", "name": "Spani Atacadista", "domain": "spani.com.br", "badge": "Atacado"},
    ],
    "sorocaba": [
        {"id": "tauste", "name": "Tauste Supermercados", "domain": "tauste.com.br", "badge": "Variedade / Ofertas"},
        {"id": "confianca", "name": "Confiança Supermercados", "domain": "confianca.com.br", "badge": "Líder Regional"},
        {"id": "sao_roque", "name": "Supermercados São Roque", "domain": "supermercadosaoroque.com.br", "badge": "Regional"},
    ],
    "rio de janeiro": [
        {"id": "guanabara", "name": "Supermercados Guanabara", "domain": "supermercadosguanabara.com.br", "badge": "Preço Baixo"},
        {"id": "zona_sul", "name": "Zona Sul", "domain": "zonasul.com.br", "badge": "Premium / Variedade"},
        {"id": "mundial", "name": "Supermercados Mundial", "domain": "supermercadosmundial.com.br", "badge": "Economia / Variedade"},
    ],
    "belo horizonte": [
        {"id": "supermercados_bh", "name": "Supermercados BH", "domain": "supermercadosbh.com.br", "badge": "Preço Baixo / Economia"},
        {"id": "verdemar", "name": "Verdemar", "domain": "verdemaratevoce.com.br", "badge": "Premium / Variedade"},
        {"id": "apoio_mineiro", "name": "Apoio Mineiro", "domain": "apoiomineiro.com.br", "badge": "Atacarejo"},
    ],
    "curitiba": [
        {"id": "muffato", "name": "Super Muffato", "domain": "delivery.supermuffato.com.br", "badge": "Regional / Variedade"},
        {"id": "condor", "name": "Condor Super Center", "domain": "condor.com.br", "badge": "Hipermercado / Ofertas"},
        {"id": "festval", "name": "Festval", "domain": "festval.com", "badge": "Premium"},
    ],
    "porto alegre": [
        {"id": "zaffari", "name": "Zaffari / Bourbon", "domain": "zaffari.com.br", "badge": "Líder / Tradição"},
        {"id": "asun", "name": "Asun Supermercados", "domain": "asun.com.br", "badge": "Preço Baixo"},
        {"id": "macromix", "name": "Macromix Atacado", "domain": "macromixatacado.com.br", "badge": "Atacarejo"},
    ],
    "florianopolis": [
        {"id": "angeloni", "name": "Angeloni", "domain": "angeloni.com.br", "badge": "Premium / Variedade"},
        {"id": "giassi", "name": "Giassi Supermercados", "domain": "giassi.com.br", "badge": "Regional / Variedade"},
        {"id": "fort_atacadista", "name": "Fort Atacadista", "domain": "fortatacadista.com.br", "badge": "Economia"},
    ],
    "brasilia": [
        {"id": "veneza", "name": "Supermercados Veneza", "domain": "supermercadosveneza.com.br", "badge": "Regional / Variedade"},
        {"id": "dona_de_casa", "name": "Super Dona de Casa", "domain": "superdonadecasa.com.br", "badge": "Preço Baixo"},
        {"id": "pao_de_acucar", "name": "Pão de Açúcar", "domain": "paodeacucar.com", "badge": "Hiper / Premium"},
    ],
    "goiania": [
        {"id": "bretas", "name": "Bretas", "domain": "bretas.com.br", "badge": "Regional / Economia"},
        {"id": "barao", "name": "Barão Supermercados", "domain": "baraodistribuidor.com.br", "badge": "Preço Baixo"},
        {"id": "atacadao", "name": "Atacadão", "domain": "atacadao.com.br", "badge": "Atacado"},
    ],
    "salvador": [
        {"id": "atakarejo", "name": "Atakarejo", "domain": "atakarejo.com.br", "badge": "Economia / Atacarejo"},
        {"id": "gbarbosa", "name": "GBarbosa", "domain": "gbarbosa.com.br", "badge": "Líder Regional"},
        {"id": "assai", "name": "Assaí Atacadista", "domain": "assai.com.br", "badge": "Atacado"},
    ],
    "fortaleza": [
        {"id": "sao_luiz", "name": "Mercadinhos São Luiz", "domain": "mercadinhossaoluiz.com.br", "badge": "Variedade / Frescor"},
        {"id": "cometa", "name": "Cometa Supermercados", "domain": "cometasupermercados.com.br", "badge": "Preço Baixo"},
        {"id": "frangolandia", "name": "Frangolândia", "domain": "frangolandia.com.br", "badge": "Regional"},
    ],
    "recife": [
        {"id": "bompreco", "name": "Bompreço", "domain": "bompreco.com.br", "badge": "Regional"},
        {"id": "arco_iris", "name": "Arco-Íris Supermercados", "domain": "arcoirissupermercados.com.br", "badge": "Preço Baixo"},
        {"id": "atacadao", "name": "Atacadão", "domain": "atacadao.com.br", "badge": "Atacado"},
    ],
    "default": [
        {"id": "redes_locais", "name": "Principais Supermercados da Região", "domain": "", "badge": "Regional"},
        {"id": "atacadao", "name": "Atacadão / Atacarejo", "domain": "atacadao.com.br", "badge": "Atacado / Economia"},
        {"id": "carrefour", "name": "Carrefour / Hipermercado", "domain": "carrefour.com.br", "badge": "Variedade & Ofertas"},
    ],
}


async def detect_location_gps(page) -> dict[str, str] | None:
    """
    Detecta localização via GPS nativo do aparelho Android usando flet-geolocator (DEC-029).
    Requer permissão ACCESS_FINE_LOCATION. Retorna dict com city/state ou None em caso de falha.
    API validada via flet-mcp: Geolocator.request_permission(), get_current_position() -> GeolocatorPosition.
    """
    try:
        from flet_geolocator import Geolocator, GeolocatorPermissionStatus

        geo = Geolocator()
        if hasattr(page, "services") and isinstance(page.services, list):
            if geo not in page.services:
                page.services.append(geo)
                page.update()

        # Solicita permissão de localização
        perm = await geo.request_permission()
        if perm not in (GeolocatorPermissionStatus.ALWAYS, GeolocatorPermissionStatus.WHILE_IN_USE):
            logger.info("[Geo] Permissão de localização negada pelo usuário.")
            return None

        # Obtém posição GPS
        position = await geo.get_current_position()
        if position is None or position.latitude is None or position.longitude is None:
            logger.info("[Geo] Posição GPS não disponível.")
            return None

        lat = float(position.latitude)
        lon = float(position.longitude)
        logger.info(f"[Geo] GPS detectou: lat={lat}, lon={lon}")

        # Reverse geocoding via Nominatim OpenStreetMap
        result = _reverse_geocode(lat, lon)
        if result:
            return result

    except ImportError:
        logger.debug("[Geo] flet-geolocator não disponível (ambiente desktop/web).")
    except Exception as exc:
        logger.warning(f"[Geo] Falha na detecção GPS: {exc}")

    return None


def _reverse_geocode(lat: float, lon: float) -> dict[str, str] | None:
    """Reverse geocoding via OpenStreetMap Nominatim para converter coordenadas em cidade/estado."""
    try:
        import httpx
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=pt-BR"
        headers = {"User-Agent": "MAIFinance/1.0 (bruno@martinsautomation.com)"}
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                address = data.get("address", {})
                city = address.get("city") or address.get("town") or address.get("municipality") or ""
                state = address.get("state", "")
                # Abreviação do estado (ex: "São Paulo" -> "SP")
                state_abbr = _abbreviate_state(state)
                neighborhood = address.get("suburb") or address.get("neighbourhood") or ""
                cep = address.get("postcode") or ""
                if city:
                    return {
                        "city": f"{city}, {state_abbr}" if state_abbr else city,
                        "state": state_abbr or "SP",
                        "neighborhood": neighborhood,
                        "cep": cep,
                    }
    except Exception as exc:
        logger.debug(f"[Geo] Reverse geocoding falhou: {exc}")
    return None


def _abbreviate_state(state_name: str) -> str:
    """Converte nome completo do estado brasileiro em abreviação de 2 letras."""
    STATES = {
        "acre": "AC", "alagoas": "AL", "amapá": "AP", "amazonas": "AM",
        "bahia": "BA", "ceará": "CE", "distrito federal": "DF",
        "espírito santo": "ES", "goiás": "GO", "maranhão": "MA",
        "mato grosso": "MT", "mato grosso do sul": "MS",
        "minas gerais": "MG", "pará": "PA", "paraíba": "PB",
        "paraná": "PR", "pernambuco": "PE", "piauí": "PI",
        "rio de janeiro": "RJ", "rio grande do norte": "RN",
        "rio grande do sul": "RS", "rondônia": "RO", "roraima": "RR",
        "santa catarina": "SC", "são paulo": "SP", "sergipe": "SE",
        "tocantins": "TO",
    }
    if not state_name:
        return ""
    normalized = state_name.strip().lower()
    # Se já é abreviação de 2 letras
    if len(normalized) == 2:
        return normalized.upper()
    return STATES.get(normalized, normalized[:2].upper())


def detect_device_location_auto() -> dict[str, str]:
    """
    Detecta automaticamente a localização geográfica (cidade e UF) do dispositivo
    em segundo plano via GeoIP com fallback multi-provedor resiliente (DEC-029).
    """
    global _configured_location
    providers = [
        _geoip_via_ip_api,
        _geoip_via_ipwho,
        _geoip_via_ipapi_co,
    ]
    for provider in providers:
        try:
            result = provider()
            if result:
                _configured_location = result
                return dict(_configured_location)
        except Exception:
            continue
    return dict(_configured_location)


def _geoip_via_ip_api() -> dict[str, str] | None:
    """Provedor GeoIP 1: ip-api.com (sem limite para uso não-comercial)."""
    try:
        import httpx
        with httpx.Client(timeout=2.5) as client:
            resp = client.get("http://ip-api.com/json/?fields=status,city,regionName,region,zip&lang=pt-BR")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    city = (data.get("city") or "").strip()
                    region = (data.get("region") or "").strip().upper()
                    if city:
                        return {
                            "city": f"{city}, {region}" if region else city,
                            "state": region or "SP",
                            "neighborhood": "",
                            "cep": (data.get("zip") or "").strip(),
                        }
    except Exception:
        pass
    return None


def _geoip_via_ipwho() -> dict[str, str] | None:
    """Provedor GeoIP 2: ipwho.is (rápido e gratuito)."""
    try:
        import httpx
        with httpx.Client(timeout=2.5) as client:
            resp = client.get("https://ipwho.is/?fields=city,region_code,postal&lang=pt-BR")
            if resp.status_code == 200:
                data = resp.json()
                city = (data.get("city") or "").strip()
                region = (data.get("region_code") or "").strip().upper()
                if city:
                    return {
                        "city": f"{city}, {region}" if region else city,
                        "state": region or "SP",
                        "neighborhood": "",
                        "cep": (data.get("postal") or "").strip(),
                    }
    except Exception:
        pass
    return None


def _geoip_via_ipapi_co() -> dict[str, str] | None:
    """Provedor GeoIP 3: ipapi.co (fallback original)."""
    try:
        import httpx
        with httpx.Client(timeout=2.5) as client:
            resp = client.get("https://ipapi.co/json/")
            if resp.status_code == 200:
                data = resp.json()
                city = (data.get("city") or "").strip()
                region = (data.get("region_code") or data.get("region") or "").strip().upper()
                if city:
                    return {
                        "city": f"{city}, {region}" if region else city,
                        "state": region or "SP",
                        "neighborhood": (data.get("org") or "").strip(),
                        "cep": (data.get("postal") or "").strip(),
                    }
    except Exception:
        pass
    return None


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

    # Remove pontuações e acentos comuns para match
    normalized = str(city).lower().replace(",", " ").replace("-", " ").strip()
    for reg_key, markets in REGIONAL_MARKETS.items():
        if reg_key != "default" and (reg_key in normalized or any(part in reg_key for part in normalized.split() if len(part) > 3)):
            return list(markets)

    # Se a cidade não for catalogada estaticamente, monta redes dinâmicas para a cidade
    clean_city_name = city.split(",")[0].strip()
    return [
        {"id": f"mercado_{clean_city_name.lower().replace(' ', '_')}", "name": f"Supermercados de {clean_city_name}", "domain": "", "badge": f"Regional ({clean_city_name})"},
        {"id": "atacadao_regional", "name": f"Atacadão / Atacarejo em {clean_city_name}", "domain": "atacadao.com.br", "badge": "Preço de Atacado"},
        {"id": "hiper_regional", "name": f"Hipermercados de {clean_city_name}", "domain": "", "badge": "Variedade & Ofertas"},
    ]
