"""Tests para validar la configuración del proyecto."""
import os
import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def setup_test_env() -> None:
    """Configurar variables de entorno para testing."""
    # Crear archivo .env temporal para tests
    test_env_content = """
SUPABASE_URL=https://test.supabase.co
SUPABASE_KEY=test_key_123456
GROUP_TARGET=-100123456789
BOT_TOKEN=test_bot_token_123456
SEND_INTERVAL_SECONDS=60
MESSAGE_DELAY_SECONDS=2
"""
    with open(".env.test", "w", encoding="utf-8") as file:
        file.write(test_env_content)
    
    # Recargar variables de entorno
    load_dotenv(".env.test", override=True)
    
    yield
    
    # Limpiar archivo temporal
    if os.path.exists(".env.test"):
        os.remove(".env.test")


def test_settings_class_exists() -> None:
    """Verifica que la clase Settings existe en config.py."""
    from config import Settings
    assert Settings is not None


def test_settings_instance_exists() -> None:
    """Verifica que la instancia settings existe."""
    from config import settings
    assert settings is not None


def test_supabase_configuration() -> None:
    """Verifica que las credenciales de Supabase se cargan correctamente."""
    from config import settings
    
    assert settings.SUPABASE_URL == "https://test.supabase.co"
    assert settings.SUPABASE_KEY == "test_key_123456"


def test_telegram_configuration() -> None:
    """Verifica que las credenciales de Telegram se cargan correctamente."""
    from config import settings
    
    assert settings.BOT_TOKEN == "test_bot_token_123456"
    assert settings.GROUP_TARGET == -100123456789


def test_behavior_configuration() -> None:
    """Verifica que las configuraciones de comportamiento se cargan correctamente."""
    from config import settings
    
    assert settings.SEND_INTERVAL_SECONDS == 60
    assert settings.MESSAGE_DELAY_SECONDS == 2.0


def test_is_configured_property() -> None:
    """Verifica que la propiedad is_configured funciona correctamente."""
    from config import settings
    
    # Con todas las variables configuradas, debería ser True
    assert settings.is_configured is True


def test_settings_repr() -> None:
    """Verifica que el método __repr__ funciona correctamente."""
    from config import settings
    
    repr_str = repr(settings)
    assert "Settings" in repr_str
    assert "supabase=✓" in repr_str
    assert "group=-100123456789" in repr_str
    assert "interval=60s" in repr_str


def test_modules_importable() -> None:
    """Verifica que todos los módulos principales pueden importarse."""
    try:
        import config  # noqa: F401
        import supabase_client  # noqa: F401
        import telegram_notifier  # noqa: F401
        assert True
    except ImportError as exc:
        pytest.fail(f"No se pudo importar módulo: {exc}")