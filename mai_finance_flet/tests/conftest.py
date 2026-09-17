"""
conftest.py — Configuração global do pytest para mai_finance_flet/tests/.
Garante que a raiz de mai_finance_flet/ esteja no sys.path
para que os módulos (config, db, services, ui) sejam importáveis nos testes.
"""
import sys
from pathlib import Path

# Adiciona mai_finance_flet/ ao path para imports absolutos nos testes
sys.path.insert(0, str(Path(__file__).parent.parent))
