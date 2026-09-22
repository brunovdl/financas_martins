"""
updater.py — Serviço de Verificação, Download e Atualização Automática do APK Android
"""
import logging
import os
import re
import sys
import tempfile
import urllib.request
from typing import Any, Callable, Optional
import httpx
import flet as ft

logger = logging.getLogger(__name__)

# Versão local do aplicativo instalada (fallback padrão se version.json não existir)
CURRENT_VERSION = "1.0.10"
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


def safe_launch_url(page: ft.Page, url: str) -> bool:
    """
    Abre uma URL de forma segura e compatível tanto com Flet 1.0+ (UrlLauncher / run_task)
    quanto com instâncias mock de testes unitários (hasattr launch_url).
    Garante o registro prévio do serviço UrlLauncher em page.services para evitar RuntimeError.
    """
    if not page or not url:
        return False

    # 1. Se page possuir launch_url (ex.: mocks de teste ou flet legado)
    if hasattr(page, "launch_url") and callable(getattr(page, "launch_url")):
        try:
            page.launch_url(url)
            return True
        except Exception as e:
            logger.warning(f"[safe_launch_url] Falha em page.launch_url: {e}")

    # 2. Garante registro de UrlLauncher em page.services no Flet 1.0+
    launcher = None
    if hasattr(page, "services") and isinstance(page.services, list):
        for s in page.services:
            if isinstance(s, ft.UrlLauncher):
                launcher = s
                break
        if not launcher:
            launcher = ft.UrlLauncher()
            page.services.append(launcher)
            try:
                page.update()
            except Exception:
                pass
    else:
        launcher = ft.UrlLauncher()

    # 3. Flet 1.0+: usa launcher.launch_url assíncrono via page.run_task
    if hasattr(page, "run_task") and callable(getattr(page, "run_task")):
        try:
            async def _launch():
                await launcher.launch_url(url)
            page.run_task(_launch)
            return True
        except Exception as e:
            logger.warning(f"[safe_launch_url] Falha em page.run_task(UrlLauncher): {e}")

    # 4. Fallback via asyncio
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(launcher.launch_url(url))
        else:
            loop.run_until_complete(launcher.launch_url(url))
        return True
    except Exception as e:
        logger.warning(f"[safe_launch_url] Falha em asyncio fallback: {e}")

    return False


def install_apk_android_native(apk_path: str) -> bool:
    """
    Aciona o PackageInstaller oficial do Android diretamente via PyJNIus / JNI (DEC-035).
    Monta Intent(ACTION_VIEW) com FileProvider e flags de permissão de leitura.
    """
    if not apk_path or not os.path.exists(apk_path):
        logger.warning(f"[Updater] APK não encontrado no caminho: {apk_path}")
        return False

    try:
        import jnius
        # Garante vinculação segura da thread atual ao JavaVM do Android
        if hasattr(jnius, "attach_thread"):
            jnius.attach_thread()

        from jnius import autoclass

        # 1. Obtém a Activity host através da variável de ambiente do Flet / SeriousPython
        activity_host_class_name = os.getenv("MAIN_ACTIVITY_HOST_CLASS_NAME")
        activity = None

        if activity_host_class_name:
            try:
                host_cls = autoclass(activity_host_class_name)
                activity = getattr(host_cls, "mActivity", None)
            except Exception as e:
                logger.warning(f"[Updater] Falha ao obter Activity via {activity_host_class_name}: {e}")

        if activity is None:
            for candidate in [
                "com.flet.serious_python_android.PythonActivity",
                "com.flet.serious_python.PythonActivity",
                "org.kivy.android.PythonActivity",
                "com.martinsautomation.mai_finance.MainActivity",
            ]:
                try:
                    c = autoclass(candidate)
                    if hasattr(c, "mActivity") and c.mActivity:
                        activity = c.mActivity
                        break
                except Exception:
                    continue

        if activity is None:
            logger.warning("[Updater] PyJNIus disponível mas nenhuma Activity ativa foi encontrada.")
            return False

        # 2. Classes do Android
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        File = autoclass("java.io.File")
        FileProvider = autoclass("androidx.core.content.FileProvider")
        Build = autoclass("android.os.Build")

        file_obj = File(os.path.abspath(apk_path))
        context = activity.getApplicationContext()
        package_name = context.getPackageName()

        # 3. URI via FileProvider (compatível com Android 7.0+ a 15)
        uri = None
        if Build.VERSION.SDK_INT >= 24:
            for auth_candidate in [
                f"{package_name}.provider",
                f"{package_name}.fileprovider",
                f"{package_name}.flutter.share_provider",
            ]:
                try:
                    uri = FileProvider.getUriForFile(context, auth_candidate, file_obj)
                    if uri:
                        break
                except Exception as auth_err:
                    logger.debug(f"[Updater] FileProvider com authority {auth_candidate} falhou: {auth_err}")
                    continue

        if uri is None:
            uri = Uri.fromFile(file_obj)

        # 4. Intent com tipo MIME oficial de instalação de pacotes APK
        intent = Intent(Intent.ACTION_VIEW)
        intent.setDataAndType(uri, "application/vnd.android.package-archive")
        # FLAG_GRANT_READ_URI_PERMISSION = 1
        intent.addFlags(1)
        # FLAG_ACTIVITY_NEW_TASK = 268435456 (0x10000000)
        intent.addFlags(268435456)

        activity.startActivity(intent)
        logger.info(f"[Updater] PackageInstaller do Android disparado com sucesso para {apk_path}")
        return True

    except Exception as exc:
        logger.warning(f"[Updater] Falha no acionamento nativo via PyJNIus: {exc}")
        return False


def share_apk_installer(page: ft.Page, apk_path: str) -> bool:
    """
    Fallback usando ft.Share para abrir a folha de ações do sistema com o APK.
    Permite ao usuário selecionar o Instalador de Pacotes do Android.
    """
    try:
        if not os.path.exists(apk_path):
            return False

        share_service = None
        if hasattr(page, "services") and isinstance(page.services, list):
            for s in page.services:
                if isinstance(s, ft.Share):
                    share_service = s
                    break
            if not share_service:
                share_service = ft.Share()
                page.services.append(share_service)
                try:
                    page.update()
                except Exception:
                    pass
        else:
            share_service = ft.Share()

        async def _share():
            await share_service.share_files(
                [
                    ft.ShareFile.from_path(
                        os.path.abspath(apk_path),
                        mime_type="application/vnd.android.package-archive",
                        name="MAI Finance Atualização",
                    )
                ]
            )

        if hasattr(page, "run_task") and callable(getattr(page, "run_task")):
            page.run_task(_share)
            return True
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_share())
            else:
                loop.run_until_complete(_share())
            return True
    except Exception as exc:
        logger.warning(f"[Updater] Falha no fallback via ft.Share: {exc}")
        return False


def launch_apk_installer(page: ft.Page, apk_path: str, download_url: Optional[str] = None) -> bool:
    """
    Abre o instalador do APK no Android (PackageInstaller) com prioridade nativa (DEC-035).
    Retorna True se acionou com sucesso, False caso contrário.
    """
    is_android = os.path.isdir("/storage/emulated/0") or "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ

    if is_android:
        # Prioridade 1: Acionamento nativo direto do PackageInstaller via PyJNIus
        if install_apk_android_native(apk_path):
            return True

        # Prioridade 2: Fallback via ft.Share com MIME de APK
        if share_apk_installer(page, apk_path):
            return True

        # Prioridade 3: Fallback via download_url se houver
        if download_url and safe_launch_url(page, download_url):
            return True

        return False

    # Ambiente Desktop / Testes
    try:
        if os.path.exists(apk_path):
            abs_path = os.path.abspath(apk_path)
            file_url = f"file://{abs_path}"
            if safe_launch_url(page, file_url):
                return True
    except Exception as e:
        logger.warning(f"[Updater] Falha ao lançar arquivo local: {e}")

    if download_url:
        if safe_launch_url(page, download_url):
            return True

    return False
