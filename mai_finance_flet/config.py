"""
config.py — Variáveis de ambiente do MAI Finance Flet.
Carrega o .env da raiz de mai_finance_flet/ (ou do diretório de trabalho).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Tenta carregar .env da pasta do projeto e da raiz do workspace
load_dotenv(Path(__file__).parent / ".env", override=False)
load_dotenv(Path(__file__).parent.parent / ".env", override=False)
load_dotenv(override=False)

# Supabase
SUPABASE_URL: str = (
    os.getenv("SUPABASE_URL")
    or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://frauytuzqpubsbijbjrt.supabase.co")
)
SUPABASE_ANON_KEY: str = (
    os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
)

# JWT caseiro — assinatura de sessão
JWT_SECRET: str = os.getenv("JWT_SECRET", "mai-finance-secure-jwt-secret-key-2026-prod-local")
SESSION_DURATION_SECONDS: int = 86_400  # 24 horas

# Groq
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Open Finance / Pluggy (adiado — pode estar vazio)
PLUGGY_CLIENT_ID: str = os.getenv("PLUGGY_CLIENT_ID", "")
PLUGGY_CLIENT_SECRET: str = os.getenv("PLUGGY_CLIENT_SECRET", "")
PLUGGY_ITEM_IDS: list[str] = [
    item.strip()
    for item in os.getenv("PLUGGY_ITEM_IDS", "").split(",")
    if item.strip()
]

# Flet Web / Container (0.0.0.0 para suportar proxy reverso/Easypanel)
FLET_HOST: str = os.getenv("FLET_HOST", "0.0.0.0")
FLET_PORT: int = int(os.getenv("PORT", os.getenv("FLET_PORT", "8550")))
