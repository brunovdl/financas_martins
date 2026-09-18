"""
test_inject_version.py — Testes do script de injeção de versão no app
"""
import json
import os
import tempfile
from unittest.mock import patch

from scripts.inject_version import inject_version


def test_inject_version_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Cria arquivos temporários simulando a estrutura
        services_dir = os.path.join(tmpdir, "services")
        os.makedirs(services_dir, exist_ok=True)
        updater_file = os.path.join(services_dir, "updater.py")
        with open(updater_file, "w", encoding="utf-8") as f:
            f.write('CURRENT_VERSION = "0.0.1"\nGITHUB_REPO = "test/repo"\n')

        # Mock de dirname do script para apontar para tmpdir/scripts
        script_dir = os.path.join(tmpdir, "scripts")
        with patch("os.path.abspath", return_value=os.path.join(script_dir, "inject_version.py")):
            inject_version("1.2.3", "45")

        # Verifica updater.py
        with open(updater_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        assert 'CURRENT_VERSION = "1.2.3"' in updated_content

        # Verifica version.json
        version_file = os.path.join(tmpdir, "version.json")
        assert os.path.exists(version_file)
        with open(version_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == {"version": "1.2.3", "build_number": "45"}

        # Verifica assets/version.json
        assets_version_file = os.path.join(tmpdir, "assets", "version.json")
        assert os.path.exists(assets_version_file)
        with open(assets_version_file, "r", encoding="utf-8") as f:
            assets_data = json.load(f)
        assert assets_data == {"version": "1.2.3", "build_number": "45"}
