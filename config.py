"""
config.py
Configuración centralizada desde variables de entorno.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)


class Settings:
    """Configuración tipada del notificador de Telegram."""

    # ── Supabase ─────────────────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # ── Telegram ─────────────────────────────────────────────────────────
    #API_ID: int = int(os.getenv("API_ID", "0"))
    #API_HASH: str = os.getenv("API_HASH", "")
    #SESSION_STRING: str = os.getenv("SESSION_STRING", "")

    GROUP_TARGET: int = int(os.getenv("GROUP_TARGET", "0"))
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # ── Comportamiento ───────────────────────────────────────────────────
    SEND_INTERVAL_SECONDS: int = int(os.getenv("SEND_INTERVAL_SECONDS", "120"))
    MESSAGE_DELAY_SECONDS: float = float(os.getenv("MESSAGE_DELAY_SECONDS", "3"))

    @property
    def is_configured(self) -> bool:
        return all([
            self.SUPABASE_URL,
            self.SUPABASE_KEY,
            self.BOT_TOKEN,
            self.GROUP_TARGET != 0,
        ])

    def __repr__(self) -> str:
        return (
            f"<Settings "
            f"supabase={'✓' if self.SUPABASE_URL else '✗'} "
            f"group={self.GROUP_TARGET} "
            f"interval={self.SEND_INTERVAL_SECONDS}s>"
        )


settings = Settings()