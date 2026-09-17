"""
test_config.py — Validação do carregamento seguro de configurações e variáveis de ambiente.
"""
import os
import importlib
from unittest.mock import patch


class TestConfig:
    """Valida resiliência de config.py para ambientes embarcados como Android."""

    def test_config_loads_without_exceptions(self):
        """Garante que a importação de config funciona sem lançar exceções."""
        import config
        assert hasattr(config, "SUPABASE_URL")
        assert hasattr(config, "SUPABASE_ANON_KEY")
        assert config.SUPABASE_URL.startswith("https://")
        assert bool(config.SUPABASE_ANON_KEY)

    def test_config_resilient_when_dotenv_fails(self):
        """Simula falha ou ausência do python-dotenv (como no Serious Python) e valida que as variáveis padrão persistem."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("dotenv.load_dotenv", side_effect=AssertionError("Simulated frame error")):
                import config
                importlib.reload(config)
                assert config.SUPABASE_URL.startswith("https://")
                assert config.SUPABASE_ANON_KEY.startswith("ey")
                assert config.JWT_SECRET != ""
