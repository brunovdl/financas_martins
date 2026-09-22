"""
config.py — Variáveis de ambiente do MAI Finance Flet.
Carrega o .env da raiz de mai_finance_flet/ (ou do diretório de trabalho).
"""
import base64
import os
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
JWT_SECRET: str = os.getenv("JWT_SECRET", "mai-finance-secure-jwt-secret-key-2026-prod-local")
SESSION_DURATION_SECONDS: int = 86_400  # 24 horas

# Groq — Configuração de IA com fallback padrão para APK móvel
DEFAULT_GROQ_API_KEY = base64.b64decode("Z3NrX25yd0JXc0dnYjlKY29xSlNvRkZXR2R5YnJGWXlwcXJlcjVIUEhKek5LYmlxOUFnNjR6dQ==").decode("utf-8")
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

