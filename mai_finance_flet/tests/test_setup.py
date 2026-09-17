"""
test_setup.py — Testes de validação do setup inicial (T-001).

@spec:AC-019 — Dockerfile Python multi-stage com usuário não-root
@spec:AC-020 — Variáveis de ambiente documentadas em .env.example
"""
import os
from pathlib import Path

# Raiz do projeto mai_finance_flet/
ROOT = Path(__file__).parent.parent
PROJECT_ROOT = ROOT.parent  # raiz do repositório


# ---------------------------------------------------------------------------
# AC-020 — Variáveis de ambiente documentadas em .env.example
# @spec:AC-020
# ---------------------------------------------------------------------------

REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "JWT_SECRET",
    "GROQ_API_KEY",
    "PLUGGY_CLIENT_ID",
    "PLUGGY_CLIENT_SECRET",
    "PLUGGY_ITEM_IDS",
]


def test_env_example_exists():
    """@spec:AC-020 — .env.example deve existir na pasta mai_finance_flet/."""
    env_example = ROOT / ".env.example"
    assert env_example.exists(), f".env.example não encontrado em {ROOT}"


def test_env_example_contains_required_vars():
    """@spec:AC-020 — .env.example deve conter todas as variáveis obrigatórias."""
    env_example = ROOT / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    missing = [v for v in REQUIRED_ENV_VARS if v not in content]
    assert not missing, f".env.example está faltando as variáveis: {missing}"


# ---------------------------------------------------------------------------
# Estrutura de pastas obrigatória
# ---------------------------------------------------------------------------

REQUIRED_DIRS = [
    "db",
    "services",
    "ui",
    "ui/components",
    "tests",
]

REQUIRED_FILES = [
    "app.py",
    "config.py",
    "requirements.txt",
    ".env.example",
    "db/supabase_client.py",
]


def test_required_directories_exist():
    """Estrutura de pastas do projeto deve estar criada."""
    missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
    assert not missing, f"Pastas ausentes: {missing}"


def test_required_files_exist():
    """Arquivos essenciais do projeto devem existir."""
    missing = [f for f in REQUIRED_FILES if not (ROOT / f).exists()]
    assert not missing, f"Arquivos ausentes: {missing}"


# ---------------------------------------------------------------------------
# AC-019 — Dockerfile Python multi-stage com usuário não-root
# @spec:AC-019
# (Este teste valida a estrutura do Dockerfile quando ele for criado na T-013.
#  Por ora marca como xfail — esperado falhar até T-013.)
# ---------------------------------------------------------------------------

def test_dockerfile_will_be_created():
    """@spec:AC-019 — Dockerfile deve existir (criado na T-013)."""
    dockerfile = ROOT / "Dockerfile"
    # Ainda não criado (T-013). Teste registra a intenção.
    if not dockerfile.exists():
        import pytest
        pytest.xfail("Dockerfile ainda não criado — será feito na T-013")
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:" in content, "Dockerfile deve usar imagem Python"
    assert "USER" in content, "Dockerfile deve definir usuário não-root"
