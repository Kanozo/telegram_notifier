"""
telegram_notifier.py
Cliente de Telegram usando Bot API (HTTP).
Funciona en PythonAnywhere sin restricciones de red.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Envía mensajes a un grupo de Telegram usando la Bot API.

    Args:
        bot_token:    Token del bot (de @BotFather).
        group_target: ID del grupo destino.
    """

    def __init__(self, bot_token: str, group_target: int) -> None:
        self._token = bot_token
        self._group_target = str(group_target)
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._is_connected = False

    async def start(self) -> None:
        """Verifica que el bot tenga acceso al grupo."""
        async with httpx.AsyncClient(timeout=15) as client:
            # Verificar conexión con getMe
            resp = await client.get(f"{self._base_url}/getMe")
            if resp.status_code != 200:
                raise RuntimeError(f"Bot token inválido: {resp.text}")

            bot_info = resp.json()
            logger.info(
                "Bot conectado: @%s (ID: %s)",
                bot_info["result"]["username"],
                bot_info["result"]["id"],
            )

            # Verificar acceso al grupo
            resp = await client.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": self._group_target,
                    "text": "✅ Notificador de URLs conectado.",
                }
            )

            if resp.status_code == 200:
                self._is_connected = True
                logger.info("Bot tiene acceso al grupo %s", self._group_target)
            else:
                error = resp.json()
                raise RuntimeError(
                    f"El bot no puede enviar mensajes al grupo {self._group_target}. "
                    f"Error: {error.get('description', 'desconocido')}. "
                    "Asegurate de agregar el bot al grupo como administrador."
                )

    async def send_message(self, message: str) -> bool:
        """
        Envía un mensaje al grupo.

        Args:
            message: Texto del mensaje.

        Returns:
            True si se envió correctamente.
        """
        if not self._is_connected:
            raise RuntimeError("Bot no conectado. Llama a start() primero.")

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/sendMessage",
                    json={
                        "chat_id": self._group_target,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    }
                )

                if resp.status_code == 200:
                    return True

                error = resp.json()
                logger.error(
                    "Error enviando mensaje: %s",
                    error.get("description", "desconocido"),
                )

                # Si es flood wait, esperar
                if resp.status_code == 429:
                    retry_after = error.get("parameters", {}).get("retry_after", 5)
                    logger.warning("Rate limit: esperando %ds...", retry_after)
                    await asyncio.sleep(retry_after)

                return False

            except httpx.RequestError as exc:
                logger.error("Error de red: %s", exc)
                return False

    async def disconnect(self) -> None:
        """Desconecta (no necesario para Bot API)."""
        if self._is_connected:
            self._is_connected = False
            logger.info("Bot desconectado.")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def __aenter__(self) -> TelegramNotifier:
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.disconnect()