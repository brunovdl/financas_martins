"""
updater.py — Serviço de Verificação, Download e Atualização Automática do APK Android
"""
import os
import re
import sys
import tempfile
import urllib.request
from typing import Any, Callable, Optional
import httpx
import flet as ft

# Versão local do aplicativo instalada
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "brunovdl/financas_martins"


def parse_version_tuple(version_str: str) -> tuple[int, ...]:
    """
    Converte strings de versão (ex: 'v1.0.5', '1.0.2', 'v1.0.12-build3') em tupla de inteiros para comparação confiável.
    """
    cleaned = version_str.strip().lstrip("vV")
    # Extrai apenas os números sequenciais
    numbers = [int(n) for n in re.findall(r"\d+", cleaned)]
    return tuple(numbers) if numbers else (0,)


def compare_versions(v1: str, v2: str) -> int:
    """
    Compara v1 e v2:
      Retorna -1 se v1 < v2 (atualização disponível)
      Retorna 0 se v1 == v2
      Retorna 1 se v1 > v2
    """
    t1 = parse_version_tuple(v1)
    t2 = parse_version_tuple(v2)

    # Iguala o comprimento das tuplas com zeros
    max_len = max(len(t1), len(t2))
    t1_padded = t1 + (0,) * (max_len - len(t1))
    t2_padded = t2 + (0,) * (max_len - len(t2))

    if t1_padded < t2_padded:
        return -1
    elif t1_padded > t2_padded:
        return 1
    return 0


def check_for_updates(
    current_version: str = CURRENT_VERSION,
    repo: str = GITHUB_REPO,
    timeout: float = 8.0,
) -> Optional[dict[str, Any]]:
    """
    Consulta a API do GitHub Releases buscando a release mais recente.
    Retorna None se não houver atualização disponível ou se falhar.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "User-Agent": "MAI-Finance-App/1.0",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            import json
            data = json.loads(resp.read().decode("utf-8"))

        tag_name = data.get("tag_name", "")
        if not tag_name:
            return None

        latest_version = tag_name.lstrip("vV")
        if compare_versions(current_version, latest_version) < 0:
            # Encontra o asset do instalador APK
            apk_asset = None
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if name.endswith(".apk"):
                    apk_asset = asset
                    break

            if apk_asset:
                return {
                    "has_update": True,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "tag_name": tag_name,
                    "release_name": data.get("name") or f"Versão {latest_version}",
                    "release_notes": data.get("body", "").strip(),
                    "apk_name": apk_asset.get("name"),
                    "apk_size_bytes": apk_asset.get("size", 0),
                    "download_url": apk_asset.get("browser_download_url"),
                    "published_at": data.get("published_at", ""),
                }
    except Exception as e:
        print(f"[Updater] Erro ao checar atualizações: {e}")

    return None


def download_apk(
    download_url: str,
    target_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, int, int], None]] = None,
    chunk_size: int = 65536,
) -> str:
    """
    Baixa o APK em streaming chamando progress_callback(percent, downloaded_bytes, total_bytes).
    Retorna o caminho do arquivo baixado.
    """
    if not target_path:
        temp_dir = tempfile.gettempdir()
        filename = download_url.split("/")[-1] or "mai_finance_update.apk"
        if not filename.endswith(".apk"):
            filename += ".apk"
        target_path = os.path.join(temp_dir, filename)

    headers = {"User-Agent": "MAI-Finance-App/1.0"}
    req = urllib.request.Request(download_url, headers=headers)

    with urllib.request.urlopen(req, timeout=30.0) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with open(target_path, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    pct = (downloaded / total_size) if total_size > 0 else 0.0
                    progress_callback(pct, downloaded, total_size)

    return target_path


def launch_apk_installer(page: ft.Page, apk_path: str, download_url: Optional[str] = None) -> None:
    """
    Abre o instalador do APK no Android.
    Se for em ambiente desktop/web, abre o link no navegador.
    """
    try:
        # Se puder lançar arquivo local no Android
        if os.path.exists(apk_path):
            abs_path = os.path.abspath(apk_path)
            # No Flet Android, launch_url abre a intent correspondente
            file_url = f"file://{abs_path}"
            page.launch_url(file_url)
            return
    except Exception as e:
        print(f"[Updater] Falha ao lançar arquivo local: {e}")

    # Fallback: abrir URL de download no navegador
    if download_url:
        page.launch_url(download_url)
