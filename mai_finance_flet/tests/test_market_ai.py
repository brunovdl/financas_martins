"""
test_market_ai.py — Testes para geolocalização e cotação inteligente de mercados com IA (T-017).

Cobre os critérios de aceite:
- @spec:AC-023 — Detecção de localização para consulta de mercados da região
- @spec:AC-024 — Cotação comparativa e seleção de mercado único para a compra
- @spec:AC-025 — Priorização de melhor custo-benefício em marcas conhecidas
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from services.geo_service import (
    get_device_location,
    set_custom_location,
    get_regional_markets,
)
from services.market_ai_service import (
    quote_shopping_list,
    call_groq_to_structure_quote,
    _get_reference_item,
)


class TestMarketAI:
    """Validação da geolocalização e motor de IA para cotação de compras."""

    @pytest.fixture(autouse=True)
    def reset_location(self):
        set_custom_location("São Paulo", "SP")
        yield
        set_custom_location("São Paulo", "SP")

    def test_geo_location_and_regional_markets(self):
        """Valida detecção de cidade e obtenção de mercados regionais (AC-023)."""
        loc = get_device_location()
        assert "city" in loc
        assert loc["city"] == "São Paulo"

        markets = get_regional_markets("São Paulo")
        assert len(markets) >= 3
        market_names = [m["name"] for m in markets]
        assert "Carrefour" in market_names
        assert "Pão de Açúcar" in market_names

    def test_set_custom_location(self):
        set_custom_location("Rio de Janeiro", "RJ")
        loc = get_device_location()
        assert loc["city"] == "Rio de Janeiro"
        assert loc["state"] == "RJ"

        markets = get_regional_markets("Rio de Janeiro")
        market_names = [m["name"] for m in markets]
        assert "Supermercados Guanabara" in market_names

        # Reseta para São Paulo
        set_custom_location("São Paulo", "SP")

    def test_quote_shopping_list_comparison(self):
        """Valida comparação de preços entre supermercados e seleção do menor total (AC-024)."""
        items = [
            {"id": "1", "name": "Arroz 5kg", "quantity": 1, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
            {"id": "2", "name": "Leite Integral", "quantity": 4, "unit": "cx", "corridor_category": "Laticínios & Frios"},
            {"id": "3", "name": "Café 500g", "quantity": 2, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
        ]

        result = quote_shopping_list(items)
        assert "markets" in result
        assert len(result["markets"]) >= 2
        assert "best_option" in result
        assert result["best_option"] is not None

        for m in result["markets"]:
            assert m["total_amount"] > 0
            assert len(m["items"]) == 3
            for item in m["items"]:
                assert "brand" in item
                assert "unit_price" in item
                assert item["unit_price"] > 0

    @patch("groq.Groq")
    @patch("config.GROQ_API_KEY", "fake-groq-key")
    def test_groq_ai_structuring_prioritizes_leading_brands(self, mock_groq_cls):
        """Valida que o Groq estrutura a cotação priorizando marcas líderes com melhor custo-benefício (AC-025)."""
        mock_groq_instance = MagicMock()
        mock_groq_cls.return_value = mock_groq_instance

        ai_response_payload = {
            "market_name": "Carrefour",
            "items": [
                {
                    "name": "Arroz",
                    "brand": "Camil",
                    "unit_price": 29.90,
                    "quantity": 1,
                    "product_title": "Arroz Tipo 1 Camil Pacote 5kg",
                },
                {
                    "name": "Café",
                    "brand": "Pilão",
                    "unit_price": 17.50,
                    "quantity": 2,
                    "product_title": "Café Torrado e Moído Pilão Tradicional 500g",
                },
            ],
        }

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(ai_response_payload)
        mock_groq_instance.chat.completions.create.return_value.choices = [mock_choice]

        items = [
            {"id": "1", "name": "Arroz", "quantity": 1, "unit": "pct"},
            {"id": "2", "name": "Café", "quantity": 2, "unit": "pct"},
        ]

        quote = call_groq_to_structure_quote("Carrefour", "carrefour", items, "Snippets de teste")
        assert quote["market_name"] == "Carrefour"
        # Total esperado: (29.90 * 1) + (17.50 * 2) = 64.90
        assert quote["total_amount"] == 64.90
        assert quote["items"][0]["brand"] == "Camil"
        assert quote["items"][1]["brand"] == "Pilão"

    def test_reference_item_fallback(self):
        ref = _get_reference_item("Detergente")
        assert ref["brand"] == "Ypê"
        assert ref["price"] > 0

    def test_quote_shopping_list_target_market(self):
        """Valida cotação exclusiva para um mercado específico escolhido pelo usuário."""
        items = [
            {"id": "1", "name": "Arroz 5kg", "quantity": 1, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
            {"id": "2", "name": "Café 500g", "quantity": 1, "unit": "pct", "corridor_category": "Mercearia & Padaria"},
        ]
        result = quote_shopping_list(items, target_market="Supermercados BH", city="Belo Horizonte, MG")
        assert result["single_market"] is True
        assert result["best_option"] == "Supermercados BH"
        assert len(result["markets"]) == 1
        assert result["markets"][0]["market_name"] == "Supermercados BH"
        assert result["location"]["city"] == "Belo Horizonte, MG"

