"""Tests básicos para validar la estructura del proyecto."""
import pytest


def test_config_imports() -> None:
    """Verifica que config.py puede importarse sin errores."""
    try:
        import config  # noqa: F401
        assert True
    except ImportError as exc:
        pytest.fail(f"No se pudo importar config: {exc}")


def test_supabase_client_structure() -> None:
    """Verifica que supabase_client.py tiene la estructura esperada."""
    try:
        import supabase_client  # noqa: F401
        assert True
    except ImportError as exc:
        pytest.fail(f"No se pudo importar supabase_client: {exc}")


def test_telegram_notifier_structure() -> None:
    """Verifica que telegram_notifier.py tiene la estructura esperada."""
    try:
        import telegram_notifier  # noqa: F401
        assert True
    except ImportError as exc:
        pytest.fail(f"No se pudo importar telegram_notifier: {exc}")


def test_env_file_syntax() -> None:
    """Verifica que .env.py tiene sintaxis Python válida."""
    import ast
    
    try:
        with open(".env.py", "r", encoding="utf-8") as file:
            content = file.read()
        ast.parse(content)
        assert True
    except SyntaxError as exc:
        pytest.fail(f"Error de sintaxis en .env.py: {exc}")
    except FileNotFoundError:
        pytest.fail("No se encontró el archivo .env.py")