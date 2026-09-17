"""
test_android_packaging.py — Validação dos assets de ícones Android e workflow do GitHub Actions
"""
import os
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


class TestAndroidPackaging:
    """Valida requisitos de empacotamento do instalador Android."""

    def test_app_icon_assets_exist(self):
        """Verifica se os arquivos de ícone padrão e Android existem nos caminhos esperados pelo Flet."""
        icon_paths = [
            BASE_DIR / "assets" / "icon.png",
            BASE_DIR / "assets" / "icon_android.png",
            BASE_DIR / "icon.png",
            BASE_DIR / "assets" / "icons" / "icon-512.png",
            BASE_DIR / "assets" / "icons" / "icon-192.png",
        ]
        for p in icon_paths:
            assert p.exists(), f"Arquivo de ícone não encontrado: {p}"

    def test_app_icon_dimensions_and_mode(self):
        """Garante que os ícones mestres possuem dimensões de alta definição (1024x1024) e modo RGBA."""
        high_res_icons = [
            BASE_DIR / "assets" / "icon.png",
            BASE_DIR / "assets" / "icon_android.png",
            BASE_DIR / "icon.png",
        ]
        for p in high_res_icons:
            with Image.open(p) as img:
                assert img.size == (1024, 1024), f"Dimensão incorreta para {p.name}: {img.size} (esperado 1024x1024)"
                assert img.mode == "RGBA", f"Modo de cor incorreto para {p.name}: {img.mode} (esperado RGBA)"

    def test_main_entrypoint_exists(self):
        """Garante que o arquivo de entrada main.py existe para o empacotador Flet Android."""
        main_py = BASE_DIR / "main.py"
        assert main_py.exists(), f"Entry point {main_py} não encontrado!"
        content = main_py.read_text(encoding="utf-8")
        assert "from app import main" in content
        assert "ft.run(" in content

    def test_github_actions_workflow_exists(self):
        """Valida que o arquivo de workflow do GitHub Actions existe."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "build_android_apk.yml"
        assert workflow_path.exists(), f"Workflow não encontrado: {workflow_path}"

    def test_github_actions_workflow_content(self):
        """Valida se o workflow contém os parâmetros críticos de build Android e branding oficial."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "build_android_apk.yml"
        content = workflow_path.read_text(encoding="utf-8")

        # Verifica triggers
        assert "workflow_dispatch:" in content
        assert "branches:" in content
        assert "main" in content
        assert "mai_finance_flet/**" in content
        assert "v*" in content

        # Verifica ferramentas
        assert "subosito/flutter-action" in content
        assert "flutter-version: '3.44.8'" in content
        assert "actions/setup-java" in content
        assert "java-version: '17'" in content

        # Verifica comando flet build apk e parâmetros essenciais
        assert "flet build apk" in content
        assert "--yes" in content
        assert "--no-rich-output" in content
        assert "--project mai_finance" in content
        assert '--product "MAI Finance"' in content
        assert "--android-adaptive-icon-background" in content
        assert "android.permission.INTERNET=true" in content
        assert "android.permission.REQUEST_INSTALL_PACKAGES=true" in content

        # Verifica artefatos e releases
        assert "actions/upload-artifact" in content
        assert "softprops/action-gh-release" in content
