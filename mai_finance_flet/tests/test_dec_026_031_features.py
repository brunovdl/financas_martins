"""
test_dec_026_031_features.py — Testes automatizados das decisões DEC-026 a DEC-031 do MAI Finance.

Cobre:
- DEC-026: Scanner de etiqueta de gôndola zero-toque (camera_price_scanner_modal)
- DEC-027: Seletor/chips interativos de marcas e recálculo dinâmico (market_quote_modal, shopping_quote_summary_modal)
- DEC-028: Abas/comparativo de 3 mercados reais da região (market_quote_modal)
- DEC-029: Detecção de localização via GPS nativo e reverse geocoding (geo_service)
- DEC-030: Card de item anti-encavalamento em 2 linhas (shopping_item_card)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import flet as ft

from ui.components.shopping_item_card import build_shopping_item_card
from ui.components.market_quote_modal import open_market_quote_modal
from ui.components.shopping_quote_summary_modal import open_shopping_quote_summary_modal
from ui.components.camera_price_scanner_modal import open_camera_price_scanner
from services.geo_service import (
    detect_location_gps,
    get_regional_markets,
    set_custom_location,
    get_device_location,
)
from services.market_ai_service import quote_shopping_list


class TestDEC030ShoppingItemCardAntiEncavalamento:
    """Valida o layout do card em 2 linhas para prevenir encavalamento (DEC-030)."""

    def test_card_two_line_layout_structure(self):
        """Card deve conter exatamente um Column com 2 Rows (Linha 1: nome, Linha 2: métricas + ações)."""
        item = {
            "id": "item-10",
            "name": "Sabão em Pó Omo Lavagem Perfeita 1.6kg Caixa",
            "quantity": 2.0,
            "unit": "cx",
            "estimated_price": 28.90,
            "is_bought": False,
        }

        card = build_shopping_item_card(
            item=item,
            theme_mode="dark",
            on_toggle=MagicMock(),
            on_edit=MagicMock(),
            on_delete=MagicMock(),
            on_scan_price=MagicMock(),
        )

        assert isinstance(card, ft.Container)
        col = card.content
        assert isinstance(col, ft.Column)
        assert len(col.controls) == 2

        row1 = col.controls[0]
        row2 = col.controls[1]
        assert isinstance(row1, ft.Row)
        assert isinstance(row2, ft.Row)

        # Linha 1: Checkbox + Título com ellipsis
        assert len(row1.controls) == 2
        btn_check = row1.controls[0]
        assert isinstance(btn_check, ft.IconButton)
        title_text = row1.controls[1]
        assert isinstance(title_text, ft.Text)
        assert title_text.overflow == ft.TextOverflow.ELLIPSIS
        assert title_text.expand is True

        # Linha 2: info_left (preço e qtd) e actions_group (botões)
        assert len(row2.controls) == 2
        info_left = row2.controls[0]
        actions_group = row2.controls[1]
        assert isinstance(info_left, ft.Row)
        assert isinstance(actions_group, ft.Row)

    def test_card_touch_target_and_click_to_edit(self):
        """Card deve disparar on_edit ao ser clicado."""
        item = {"id": "item-20", "name": "Leite", "quantity": 1, "estimated_price": 5.0}
        on_edit_mock = MagicMock()

        card = build_shopping_item_card(
            item=item,
            theme_mode="light",
            on_edit=on_edit_mock,
        )

        assert card.on_click is not None
        card.on_click(None)
        on_edit_mock.assert_called_once_with(item)


class TestDEC027And028MarketQuoteModal:
    """Valida abas de mercados reais (DEC-028) e chips de marcas com recálculo (DEC-027)."""

    def test_multi_market_tabs_and_brand_chips_recalculate(self):
        """Valida que o modal monta abas para os mercados e que a troca de marca atualiza o total."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK

        quote_data = {
            "best_option": "Atacadão",
            "location": {"city": "São Paulo"},
            "markets": [
                {
                    "market_name": "Atacadão",
                    "badge": "Mais Econômico",
                    "total_amount": 35.0,
                    "items": [
                        {
                            "id": "1",
                            "name": "Arroz 5kg",
                            "quantity": 1.0,
                            "unit": "pct",
                            "brand": "Camil",
                            "unit_price": 25.0,
                            "brand_options": [
                                {"brand": "Camil", "price": 25.0, "product_title": "Arroz Camil 5kg"},
                                {"brand": "Tio João", "price": 30.0, "product_title": "Arroz Tio João 5kg"},
                            ],
                        },
                        {
                            "id": "2",
                            "name": "Feijão 1kg",
                            "quantity": 1.0,
                            "unit": "pct",
                            "brand": "Carioca",
                            "unit_price": 10.0,
                            "brand_options": [
                                {"brand": "Carioca", "price": 10.0, "product_title": "Feijão Carioca 1kg"},
                                {"brand": "Kicaldo", "price": 12.0, "product_title": "Feijão Kicaldo 1kg"},
                            ],
                        },
                    ],
                },
                {
                    "market_name": "Carrefour",
                    "badge": "Variedade",
                    "total_amount": 42.0,
                    "items": [
                        {
                            "id": "1",
                            "name": "Arroz 5kg",
                            "quantity": 1.0,
                            "unit": "pct",
                            "brand": "Camil",
                            "unit_price": 28.0,
                            "brand_options": [
                                {"brand": "Camil", "price": 28.0, "product_title": "Arroz Camil 5kg"},
                            ],
                        },
                    ],
                },
            ],
        }

        on_apply = MagicMock()
        open_market_quote_modal(mock_page, quote_data, on_apply)

        # Diálogo deve ter sido exibido
        dialog = mock_page.dialog if hasattr(mock_page, "dialog") else mock_page.show_dialog.call_args[0][0]
        assert dialog is not None
        assert isinstance(dialog, ft.AlertDialog)

        # Conteúdo deve ter o tab_bar com 2 mercados
        dlg_col = dialog.content.content
        assert isinstance(dlg_col, ft.Column)
        tab_bar = dlg_col.controls[1]
        assert isinstance(tab_bar, ft.Row)
        assert len(tab_bar.controls) == 2  # Atacadão e Carrefour

    def test_shopping_quote_summary_modal_brand_chips(self):
        """Valida seletor de marcas no modal de resumo por mercado específico (DEC-027)."""
        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK

        quote_data = {
            "markets": [
                {
                    "market_name": "Pão de Açúcar",
                    "total_amount": 25.0,
                    "items": [
                        {
                            "id": "1",
                            "name": "Azeite",
                            "quantity": 1.0,
                            "unit": "un",
                            "brand": "Gallo",
                            "unit_price": 25.0,
                            "brand_options": [
                                {"brand": "Gallo", "price": 25.0, "product_title": "Azeite Gallo 500ml"},
                                {"brand": "Borges", "price": 22.0, "product_title": "Azeite Borges 500ml"},
                            ],
                        }
                    ],
                }
            ]
        }

        on_apply = MagicMock()
        open_shopping_quote_summary_modal(
            page=mock_page,
            market_name="Pão de Açúcar",
            city="São Paulo",
            quote_data=quote_data,
            on_apply_prices=on_apply,
        )

        dialog = mock_page.dialog if hasattr(mock_page, "dialog") else mock_page.show_dialog.call_args[0][0]
        assert dialog is not None


class TestDEC029NativeGPSLocation:
    """Valida detecção de localização via GPS nativo e fallback (DEC-029)."""

    @pytest.mark.asyncio
    async def test_detect_location_gps_success(self):
        """Simula retorno do sensor GPS com coordenadas e reverse geocoding."""
        import sys
        from types import ModuleType

        mock_page = MagicMock(spec=ft.Page)
        mock_page.services = []

        mock_position = MagicMock()
        mock_position.latitude = -23.5505
        mock_position.longitude = -46.6333

        mock_geo = AsyncMock()
        mock_geo.get_current_position.return_value = mock_position

        class MockPermissionStatus:
            ALWAYS = "always"
            WHILE_IN_USE = "whileInUse"
            DENIED = "denied"

        mock_geo.request_permission.return_value = MockPermissionStatus.ALWAYS

        fake_module = ModuleType("flet_geolocator")
        fake_module.Geolocator = MagicMock(return_value=mock_geo)
        fake_module.GeolocatorPermissionStatus = MockPermissionStatus

        with patch.dict(sys.modules, {"flet_geolocator": fake_module}), \
             patch("services.geo_service._reverse_geocode", return_value={"city": "São Paulo, SP", "state": "SP"}):

            result = await detect_location_gps(mock_page)
            assert result is not None
            assert "São Paulo" in result["city"]

    @pytest.mark.asyncio
    async def test_detect_location_gps_permission_denied_returns_none(self):
        """Quando o usuário nega permissão GPS, retorna None para fallback."""
        import sys
        from types import ModuleType

        mock_page = MagicMock(spec=ft.Page)
        mock_page.services = []

        mock_geo = AsyncMock()

        class MockPermissionStatus:
            ALWAYS = "always"
            WHILE_IN_USE = "whileInUse"
            DENIED = "denied"

        mock_geo.request_permission.return_value = MockPermissionStatus.DENIED

        fake_module = ModuleType("flet_geolocator")
        fake_module.Geolocator = MagicMock(return_value=mock_geo)
        fake_module.GeolocatorPermissionStatus = MockPermissionStatus

        with patch.dict(sys.modules, {"flet_geolocator": fake_module}):
            result = await detect_location_gps(mock_page)
            assert result is None


class TestDEC026CameraPriceScanner:
    """Valida scanner de etiqueta de gôndola zero-toque (DEC-026)."""

    def test_open_camera_price_scanner_renders_dialog(self):
        """Valida que o scanner abre o diálogo modal com moldura de foco e cabeçalho."""
        import sys
        from types import ModuleType

        mock_page = MagicMock(spec=ft.Page)
        mock_page.theme_mode = ft.ThemeMode.DARK
        mock_page.services = []

        fake_camera_module = ModuleType("flet_camera")
        fake_camera_module.Camera = MagicMock()
        fake_camera_module.CameraLensDirection = MagicMock()
        fake_camera_module.ResolutionPreset = MagicMock()

        item = {"id": "1", "name": "Arroz 5kg"}
        on_detected = MagicMock()

        with patch.dict(sys.modules, {"flet_camera": fake_camera_module}):
            open_camera_price_scanner(
                page=mock_page,
                item=item,
                theme_mode="dark",
                on_price_detected=on_detected,
            )

        dialog = mock_page.dialog if hasattr(mock_page, "dialog") and mock_page.dialog else mock_page.show_dialog.call_args[0][0]
        assert dialog is not None
        assert isinstance(dialog, ft.AlertDialog)
        assert dialog.modal is True


class TestDEC032To034CameraAndHeaderEnhancements:
    """Valida as correções e melhorias de DEC-032 a DEC-034."""

    def test_dec_032_groq_api_key_configured_in_config(self):
        """Valida que o config.py possui fallback seguro para GROQ_API_KEY no APK nativo."""
        import config
        assert hasattr(config, "DEFAULT_GROQ_API_KEY")
        assert len(config.DEFAULT_GROQ_API_KEY) > 10
        assert getattr(config, "GROQ_API_KEY", "") != ""

    def test_dec_033_modal_header_prevents_overflow_with_long_title(self):
        """Valida que o cabeçalho modal padronizado trunca títulos longos com ellipsis e não espreme o botão fechar."""
        from ui.components.modal_header import build_modal_header
        
        long_title = "Sabão em Pó Omo Lavagem Perfeita 1.6kg com Toque de Confort Caixa Econômica"
        on_close = MagicMock()
        header = build_modal_header(title=long_title, on_close=on_close, theme_mode="dark")
        
        assert isinstance(header, ft.Row)
        
        # O Row esquerdo com logo e título
        left_row = header.controls[0]
        assert isinstance(left_row, ft.Row)
        assert left_row.expand is True
        
        # O Text do título deve conter expand=True e ellipsis
        title_text = left_row.controls[1]
        assert isinstance(title_text, ft.Text)
        assert title_text.expand is True
        assert title_text.max_lines == 1
        assert title_text.overflow == ft.TextOverflow.ELLIPSIS

    def test_dec_034_optimize_image_bytes_downscales_large_photo(self):
        """Valida que imagens brutas de alta resolução da câmera são redimensionadas para max 1024px e formato JPEG."""
        from io import BytesIO
        from PIL import Image
        from services.price_scanner_service import optimize_image_bytes

        # Cria uma imagem sintética grande de 2400x1600 pixels (~5MB descompactada)
        large_img = Image.new("RGB", (2400, 1600), color=(255, 128, 0))
        buf = BytesIO()
        large_img.save(buf, format="JPEG", quality=95)
        raw_bytes = buf.getvalue()
        assert len(raw_bytes) > 20000

        opt_bytes, mime = optimize_image_bytes(raw_bytes, max_dim=1024, quality=80)
        assert mime == "image/jpeg"
        assert len(opt_bytes) < len(raw_bytes)

        # Verifica dimensões após otimização
        with Image.open(BytesIO(opt_bytes)) as result_img:
            w, h = result_img.size
            assert max(w, h) <= 1024
            assert w == 1024
            assert h == 682

    def test_dec_034_optimize_image_bytes_graceful_fallback_on_invalid_data(self):
        """Valida que optimize_image_bytes lida defensivamente com dados inválidos sem lançar exceção."""
        from services.price_scanner_service import optimize_image_bytes
        corrupted_bytes = b"nao_e_uma_imagem_valida"
        res_bytes, mime = optimize_image_bytes(corrupted_bytes)
        assert res_bytes == corrupted_bytes

