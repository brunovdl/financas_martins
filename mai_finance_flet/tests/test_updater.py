"""
test_updater.py — Testes Unitários do Serviço de Auto-Update e Modal de Atualização
"""
import json
from unittest.mock import MagicMock, patch
import pytest
import flet as ft

from services.updater import (
    parse_version_tuple,
    compare_versions,
    check_for_updates,
    download_apk,
    launch_apk_installer,
    CURRENT_VERSION,
)
from ui.components.update_modal import open_update_dialog


class TestUpdaterService:
    """Valida a lógica de comparação de versões e parsing do auto-updater."""

    def test_parse_version_tuple(self):
        assert parse_version_tuple("1.0.0") == (1, 0, 0)
        assert parse_version_tuple("v1.0.12") == (1, 0, 12)
        assert parse_version_tuple("V2.5.0-build4") == (2, 5, 0, 4)
        assert parse_version_tuple("invalid") == (0,)

    def test_compare_versions(self):
        # Versão mais recente disponível -> -1
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.2", "1.0.10") == -1
        assert compare_versions("v1.0.5", "v1.0.6") == -1
        assert compare_versions("1.0", "1.0.1") == -1

        # Mesma versão -> 0
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("v1.2.3", "1.2.3") == 0

        # Versão atual é mais recente que a remota -> 1
        assert compare_versions("1.0.5", "1.0.2") == 1
        assert compare_versions("v2.0.0", "v1.9.9") == 1

    @patch("urllib.request.urlopen")
    def test_check_for_updates_found(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        payload = {
            "tag_name": "v1.0.5",
            "name": "MAI Finance v1.0.5",
            "body": "Novas correções e melhorias de UI.",
            "published_at": "2026-09-17T18:00:00Z",
            "assets": [
                {
                    "name": "MAI-Finance-v1.0.5-build12.apk",
                    "size": 19500000,
                    "browser_download_url": "https://github.com/brunovdl/financas_martins/releases/download/v1.0.5/app.apk",
                }
            ],
        }
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = check_for_updates(current_version="1.0.0")
        assert res is not None
        assert res["has_update"] is True
        assert res["latest_version"] == "1.0.5"
        assert res["apk_name"] == "MAI-Finance-v1.0.5-build12.apk"
        assert "app.apk" in res["download_url"]

    @patch("urllib.request.urlopen")
    def test_check_for_updates_already_latest(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        payload = {
            "tag_name": "v1.0.0",
            "name": "MAI Finance v1.0.0",
            "assets": [{"name": "app.apk", "browser_download_url": "http://..."}],
        }
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = check_for_updates(current_version="1.0.0")
        assert res is None

    @patch("urllib.request.urlopen")
    def test_check_for_updates_no_apk(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        payload = {
            "tag_name": "v1.0.5",
            "assets": [{"name": "source.zip", "browser_download_url": "http://..."}],
        }
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = check_for_updates(current_version="1.0.0")
        assert res is None


class TestUpdateModalUI:
    """Valida a renderização e controles do diálogo de atualização."""

    def test_open_update_dialog_renders_correctly(self):
        page = MagicMock(spec=ft.Page)
        page.theme_mode = ft.ThemeMode.DARK
        page.show_dialog = MagicMock()
        page.update = MagicMock()

        update_info = {
            "current_version": "1.0.0",
            "latest_version": "1.0.5",
            "download_url": "https://example.com/app.apk",
            "apk_size_bytes": 15000000,
            "release_notes": "Correções e melhorias visuais.",
        }

        open_update_dialog(page, update_info)

        # Garante que show_dialog ou page.dialog foi acionado
        assert page.show_dialog.called or page.dialog is not None
        if page.show_dialog.called:
            dlg = page.show_dialog.call_args[0][0]
        else:
            dlg = page.dialog

        assert isinstance(dlg, ft.AlertDialog)
        assert dlg.modal is True
        assert dlg.content is not None
