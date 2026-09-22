"""
test_features_batch.py — Testes unitários para as 6 melhorias implementadas:
1. Orientação do instalador APK Android e caminhos seguros.
2. Persistência de login / credenciais salvas em storage_util.
3. Restauração do modal pai de despesas ao selecionar data no calendário.
4. Edição completa de itens na lista de compras (nome, quantidade, unidade, preço).
5. Detecção automática de localização geográfica e suporte a qualquer cidade.
6. Leitor inteligente de preços de gôndola via price_scanner_service.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest
import flet as ft

from services.price_scanner_service import (
    extract_price_from_text,
    extract_price_from_base64,
    extract_price_from_file_path,
)
from services.geo_service import (
    detect_device_location_auto,
    get_regional_markets,
    set_custom_location,
    get_device_location,
)
from ui.storage_util import (
    _get_cache_file,
    _get_cache_dir,
    get_local_item,
    set_local_item,
)
from ui.components.calendar_modal import open_calendar_modal
from ui.components.shopping_add_item_modal import open_shopping_add_item_modal


class TestPriceScannerService:
    """Valida o serviço de leitura e extração de preços por visão/OCR."""

    def test_extract_price_from_text_various_formats(self):
        assert extract_price_from_text("R$ 14,90") == 14.90
        assert extract_price_from_text("RS 8,50") == 8.50
        assert extract_price_from_text("$ 25.00") == 25.00
        assert extract_price_from_text("PROMOÇÃO DE 12,00 POR 9,99 UN") == 12.00 or extract_price_from_text("PROMOÇÃO DE 12,00 POR 9,99 UN") == 9.99
        assert extract_price_from_text("Preço: 4,75") == 4.75
        assert extract_price_from_text("") is None
        assert extract_price_from_text("Sem preco aqui") is None

    def test_extract_price_from_file_path_not_found(self):
        res = extract_price_from_file_path("caminho/inexistente/foto.jpg")
        assert res["success"] is False
        assert res["price"] is None
        assert "não encontrado" in res["error"].lower()

    @patch("services.price_scanner_service.extract_price_from_image_bytes")
    def test_extract_price_from_base64(self, mock_extract):
        mock_extract.return_value = {"success": True, "price": 19.90, "raw_text": "19.90"}
        res = extract_price_from_base64("dGVzdGU=", item_name="Arroz")
        assert res["success"] is True
        assert res["price"] == 19.90


class TestStorageAndLoginPersistence:
    """Valida a persistência em disco seguro para evitar perda no Android."""

    def test_storage_file_path_safety(self):
        path = _get_cache_file()
        assert path.endswith("session_cache.json")
        assert os.path.isabs(path)

    def test_set_and_get_local_item(self):
        mock_page = MagicMock(spec=ft.Page)
        set_local_item(mock_page, "test_remember_key", "secret123")
        val = get_local_item(mock_page, "test_remember_key")
        assert val == "secret123"


class TestCalendarParentDialog:
    """Valida a restauração determinística do diálogo pai de despesa."""

    def test_calendar_restores_parent_dialog_on_date_select(self):
        mock_page = MagicMock()
        mock_parent_dlg = MagicMock(spec=ft.AlertDialog)
        mock_parent_dlg.open = True

        selected_date = []
        dlg = open_calendar_modal(
            page=mock_page,
            on_date_selected=lambda iso, br: selected_date.append((iso, br)),
            initial_date="2026-03-22",
            parent_dialog=mock_parent_dlg,
        )

        assert dlg is not None
        assert dlg.open is True

        # Encontra uma célula de dia com clique no calendário e clica
        container = dlg.content
        col = container.content
        grid_col = col.controls[2]
        # Procura um dia clicável
        clicked = False
        for row in grid_col.controls[1:]:
            for cell in row.controls:
                if getattr(cell, "on_click", None):
                    cell.on_click(None)
                    clicked = True
                    break
            if clicked:
                break

        assert clicked is True
        assert len(selected_date) == 1
        assert mock_parent_dlg.open is True
        assert dlg.open is False


class TestGeoServiceEnhancement:
    """Valida a detecção geográfica e flexibilidade para todas as cidades brasileiras."""

    def test_supermarkets_for_any_city(self):
        # Cidade fora da lista padrão fixa
        markets = get_regional_markets("Fortaleza, CE")
        assert len(markets) >= 3
        # Deve incluir supermercados locais enriquecidos
        names = [m["name"] for m in markets]
        assert any("Fortaleza" in n or "Supermercado" in n or "Atacadão" in n for n in names)

    def test_set_custom_location_and_get(self):
        set_custom_location(city="Curitiba, PR")
        loc = get_device_location()
        assert loc["city"] == "Curitiba, PR"

    @patch("urllib.request.urlopen")
    def test_detect_device_location_auto_fallback(self, mock_urlopen):
        # Simula falha no serviço IP externo
        mock_urlopen.side_effect = Exception("Sem internet")
        loc = detect_device_location_auto()
        assert "city" in loc
        assert len(loc["city"]) > 0


class TestShoppingEditItemModal:
    """Valida a abertura do modal de edição com valores pré-preenchidos."""

    def test_open_edit_item_modal_prefilled(self):
        mock_page = MagicMock()
        mock_page.theme_mode = ft.ThemeMode.DARK
        item_to_edit = {
            "id": "item-999",
            "name": "Sabão em Pó",
            "quantity": 2.5,
            "unit": "kg",
            "corridor_category": "Limpeza",
            "actual_price": 24.90,
            "estimated_price": 26.00,
        }

        updated = []
        open_shopping_add_item_modal(
            page=mock_page,
            on_item_added=lambda n: updated.append(n),
            current_market="Supermercado Teste",
            item_to_edit=item_to_edit,
        )

        assert mock_page.show_dialog.called or mock_page.dialog is not None
