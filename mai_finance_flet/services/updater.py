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

# Versão local do aplicativo instalada (fallback padrão se version.json não existir)
CURRENT_VERSION = "1.0.9"
GITHUB_REPO = "brunovdl/financas_martins"


def get_current_app_version() -> str:
    """
    Retorna a versão oficial instalada do aplicativo.
    Prioriza leitura de version.json gerado no build Android, com fallback para CURRENT_VERSION.
    """
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "version.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "version.json"),
        os.path.join(os.getcwd(), "version.json"),
        os.path.join(os.getcwd(), "assets", "version.json"),
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    import json
                    data = json.load(f)
                    ver = data.get("version")
                    if ver:
                        return str(ver).strip().lstrip("vV")
        except Exception:
            pass

    return CURRENT_VERSION.lstrip("vV")


def get_android_download_dir() -> str:
    """
    Retorna o diretório de Downloads ideal para a plataforma.
    No Android, prioriza a pasta pública '/storage/emulated/0/Download' para que
    o APK fique acessível ao instalador nativo do sistema e ao usuário.
    """
    android_public_downloads = [
        "/storage/emulated/0/Download",
        "/sdcard/Download",
        "/storage/self/primary/Download",
    ]
    for p in android_public_downloads:
        if os.path.isdir(p):
            return p

    # Se estiver em ambiente Desktop, tenta pasta Downloads do usuário
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.isdir(user_downloads):
        return user_downloads

    return tempfile.gettempdir()


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
    current_version: Optional[str] = None,
    repo: str = GITHUB_REPO,
    timeout: float = 8.0,
) -> Optional[dict[str, Any]]:
    """
    Consulta a API do GitHub Releases buscando a release mais recente.
    Retorna None se não houver atualização disponível ou se falhar.
    """
    cur_ver = current_version or get_current_app_version()
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
        if compare_versions(cur_ver, latest_version) < 0:
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
                    "current_version": cur_ver,
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
    Salva na pasta de Downloads pública do Android por padrão.
    Retorna o caminho do arquivo baixado.
    """
    if not target_path:
        dest_dir = get_android_download_dir()
        filename = download_url.split("/")[-1] or "mai_finance_update.apk"
        if not filename.endswith(".apk"):
            filename += ".apk"
        target_path = os.path.join(dest_dir, filename)

    headers = {"User-Agent": "MAI-Finance-App/1.0"}
    req = urllib.request.Request(download_url, headers=headers)

    with urllib.request.urlopen(req, timeout=60.0) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        # Cria pasta se não existir
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

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


def launch_apk_installer(page: ft.Page, apk_path: str, download_url: Optional[str] = None) -> bool:
    """
    Abre o instalador do APK no Android.
    Retorna True se acionou com sucesso, False caso contrário.
    """
    try:
        if os.path.exists(apk_path):
            abs_path = os.path.abspath(apk_path)
            # Tenta disparar intent de visualização de arquivo
            file_url = f"file://{abs_path}"
            page.launch_url(file_url)
            return True
    except Exception as e:
        print(f"[Updater] Falha ao lançar arquivo local: {e}")

    if download_url:
        try:
            page.launch_url(download_url)
            return True
        except Exception:
            pass

    return False
