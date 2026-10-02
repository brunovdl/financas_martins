"""
config.py — Variáveis de ambiente do MAI Finance Flet.
Carrega o .env da raiz de mai_finance_flet/ (ou do diretório de trabalho).
"""
import os
import secrets
from pathlib import Path
# Carregamento seguro do .env (apenas se os arquivos existirem)
# Evita chamadas sem path (find_dotenv) que causam AssertionError em runtimes embarcados (Android Serious Python)
try:
    from dotenv import load_dotenv

    for env_path in [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]:
        try:
            if env_path.exists() and env_path.is_file():
                load_dotenv(dotenv_path=env_path, override=False)
        except Exception:
            pass
except Exception:
    pass

# Supabase — Configurações padrão de produção públicas para o app móvel nativo
# (equivalente às variáveis públicas expostas no frontend web)
DEFAULT_SUPABASE_URL = "https://frauytuzqpubsbijbjrt.supabase.co"
DEFAULT_SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyYXV5dHV6cXB1YnNiaWpianJ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4NDg5OTgsImV4cCI6MjA3NTQyNDk5OH0."
    "rV-3lA6J33VWnsVlY5lTXqN5bERads0O2R8al9UmPTQ"
)

SUPABASE_URL: str = (
    os.getenv("SUPABASE_URL")
    or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    or DEFAULT_SUPABASE_URL
)
SUPABASE_ANON_KEY: str = (
    os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    or DEFAULT_SUPABASE_ANON_KEY
)

# JWT caseiro — assinatura de sessão
# Ordem: variável de ambiente > segredo aleatório gerado e persistido no diretório
# de dados do app (estável entre reinícios e atualizações do APK). Nunca hard-coded.
_JWT_SECRET_FILENAME = "jwt_secret"


def _local_data_dirs() -> list[Path]:
    dirs: list[Path] = []
    flet_storage = os.environ.get("FLET_APP_STORAGE_DATA")
    if flet_storage:
        dirs.append(Path(flet_storage) / ".mai_finance")
    # Sandbox do app no Android (persiste entre atualizações do APK)
    for android_dir in (
        os.environ.get("ANDROID_DATA"),
        "/data/data/com.martinsautomation.mai_finance/files",
        "/data/user/0/com.martinsautomation.mai_finance/files",
    ):
        if android_dir and os.path.isdir(android_dir):
            dirs.append(Path(android_dir) / ".mai_finance")
    try:
        home = Path.home()
        if str(home) not in ("", "/"):
            dirs.append(home / ".mai_finance")
    except Exception:
        pass
    dirs.append(Path(__file__).parent / ".mai_cache")
    return dirs


def _load_or_create_local_secret() -> str:
    for directory in _local_data_dirs():
        secret_file = directory / _JWT_SECRET_FILENAME
        try:
            if secret_file.is_file():
                existing = secret_file.read_text(encoding="utf-8").strip()
                if len(existing) >= 32:
                    return existing
            directory.mkdir(parents=True, exist_ok=True)
            new_secret = secrets.token_urlsafe(48)
            secret_file.write_text(new_secret, encoding="utf-8")
            try:
                os.chmod(secret_file, 0o600)
            except Exception:
                pass
            return new_secret
        except Exception:
            continue
    # Último recurso: segredo apenas em memória (sessões não sobrevivem a reinício)
    return secrets.token_urlsafe(48)


JWT_SECRET: str = os.getenv("JWT_SECRET") or _load_or_create_local_secret()
SESSION_DURATION_SECONDS: int = 86_400  # 24 horas
REMEMBER_DURATION_SECONDS: int = 30 * 86_400  # "Lembrar de mim": 30 dias

# Groq — a chave NUNCA fica no código-fonte. No APK, o CI injeta o secret
# GROQ_API_KEY nesta linha durante o build; localmente/web, use a variável de ambiente.
DEFAULT_GROQ_API_KEY = ""
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY") or DEFAULT_GROQ_API_KEY

# Open Finance / Pluggy (adiado — pode estar vazio)
PLUGGY_CLIENT_ID: str = os.getenv("PLUGGY_CLIENT_ID", "")
PLUGGY_CLIENT_SECRET: str = os.getenv("PLUGGY_CLIENT_SECRET", "")
PLUGGY_ITEM_IDS: list[str] = [
    item.strip()
    for item in os.getenv("PLUGGY_ITEM_IDS", "").split(",")
    if item.strip()
]

# Flet Web / Container (127.0.0.1 para dev local; 0.0.0.0 em container/Easypanel via ENV)
FLET_HOST: str = os.getenv("FLET_HOST", "127.0.0.1")
FLET_PORT: int = int(os.getenv("PORT", os.getenv("FLET_PORT", "8550")))

