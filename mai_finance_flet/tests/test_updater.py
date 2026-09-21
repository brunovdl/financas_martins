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
    get_current_app_version,
    get_android_download_dir,
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

    def test_get_current_app_version_from_json(self):
        fake_json = '{"version": "1.0.15", "build": 15}'
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", unittest_mock_open := MagicMock()):
                unittest_mock_open.return_value.__enter__.return_value.read.return_value = fake_json
                with patch("json.load", return_value={"version": "1.0.15"}):
                    v = get_current_app_version()
                    assert v == "1.0.15"

    def test_get_current_app_version_fallback(self):
        with patch("os.path.exists", return_value=False):
            v = get_current_app_version()
            assert v == CURRENT_VERSION.lstrip("vV")

    def test_get_android_download_dir_android(self):
        with patch("os.path.isdir") as mock_isdir:
            # Simula que /storage/emulated/0/Download existe
            def fake_isdir(path):
                return path == "/storage/emulated/0/Download"
            mock_isdir.side_effect = fake_isdir

            d = get_android_download_dir()
            assert d == "/storage/emulated/0/Download"

    def test_get_android_download_dir_fallback(self):
        with patch("os.path.isdir", return_value=False):
            with patch("tempfile.gettempdir", return_value="/custom/temp"):
                d = get_android_download_dir()
                assert d == "/custom/temp"

    def test_launch_apk_installer_file_exists(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.launch_url = MagicMock()

        with patch("os.path.exists", return_value=True):
            success = launch_apk_installer(mock_page, "/storage/Download/app.apk")
            assert success is True
            assert mock_page.launch_url.called
            called_url = mock_page.launch_url.call_args[0][0]
            assert called_url.startswith("file://")

    def test_launch_apk_installer_browser_fallback(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.launch_url = MagicMock()

        with patch("os.path.exists", return_value=False):
            success = launch_apk_installer(
                mock_page, "/storage/Download/app.apk", download_url="https://github.com/releases/app.apk"
            )
            assert success is True
            mock_page.launch_url.assert_called_with("https://github.com/releases/app.apk")

    def test_launch_apk_installer_failure(self):
        mock_page = MagicMock(spec=ft.Page)
        with patch("os.path.exists", return_value=False):
            success = launch_apk_installer(mock_page, "/non_existent.apk", download_url=None)
            assert success is False

    def test_launch_apk_installer_android_prioritizes_download_url(self):
        mock_page = MagicMock(spec=ft.Page)
        mock_page.launch_url = MagicMock()

        # Simula ambiente Android
        with patch("os.path.isdir", return_value=True):
            success = launch_apk_installer(
                mock_page,
                "/storage/emulated/0/Download/app.apk",
                download_url="https://github.com/releases/app.apk",
            )
            assert success is True
            mock_page.launch_url.assert_called_with("https://github.com/releases/app.apk")

    @patch("urllib.request.urlopen")
    def test_download_apk_progress(self, mock_urlopen, tmp_path):
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Length": "100"}
        mock_resp.read.side_effect = [b"a" * 50, b"b" * 50, b""]
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        progress_records = []
        def on_prog(pct, down, tot):
            progress_records.append((pct, down, tot))

        target_file = str(tmp_path / "test.apk")
        result = download_apk(
            "https://example.com/app.apk",
            target_path=target_file,
            progress_callback=on_prog,
            chunk_size=50,
        )

        assert result == target_file
        assert len(progress_records) == 2
        assert progress_records[-1] == (1.0, 100, 100)

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

    def test_dashboard_web_updater_behavior(self):
        """Valida que o Dashboard desabilita verificações de atualização quando executando no navegador Web."""
        from ui.dashboard_view import DashboardView

        # Cenário 1: Ambiente Web (page.web = True)
        mock_page_web = MagicMock(spec=ft.Page)
        mock_page_web.web = True
        mock_page_web.width = 1200
        mock_page_web.theme_mode = ft.ThemeMode.DARK
        mock_page_web.snack_bar = None
        mock_page_web.update = MagicMock()

        view_web = DashboardView(page=mock_page_web)
        assert view_web._is_web() is True
        assert view_web.btn_check_update.visible is False
        assert view_web.item_check_update.visible is False

        # Chamada manual em ambiente Web exibe aviso amigável sem chamar a API do GitHub
        view_web._manual_check_update()
        assert mock_page_web.snack_bar is not None
        assert "Web" in mock_page_web.snack_bar.content.value

        # Cenário 2: Ambiente Nativo / Mobile / Desktop (page.web = False)
        mock_page_native = MagicMock(spec=ft.Page)
        mock_page_native.web = False
        mock_page_native.width = 1200
        mock_page_native.theme_mode = ft.ThemeMode.DARK

        view_native = DashboardView(page=mock_page_native)
        assert view_native._is_web() is False
        assert view_native.btn_check_update.visible is True
        assert view_native.item_check_update.visible is True


