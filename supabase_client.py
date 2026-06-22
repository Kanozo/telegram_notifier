"""
supabase_client.py
Cliente Supabase para leer URLs pendientes y marcarlas como enviadas.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from supabase import Client, create_client

from config import settings

logger = logging.getLogger(__name__)


class PendingUrl(BaseModel):
    """URL pendiente de envío a Telegram."""
    id: int
    url: str
    keyword: Optional[str] = None
    send_tg: bool = False


class SupabaseUrlReader:
    """
    Lee URLs pendientes de la tabla `url` donde `send_tg = false`.
    Las marca como enviadas después de notificar a Telegram.
    """

    def __init__(self) -> None:
        self._client: Client | None = None

    async def connect(self) -> None:
        """Inicializa la conexión a Supabase."""
        try:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
            )
            logger.info("Supabase conectado: %s", settings.SUPABASE_URL[:50])
        except Exception as exc:
            logger.error("Error conectando a Supabase: %s", exc)
            raise

    async def disconnect(self) -> None:
        """Cierra la conexión a Supabase."""
        if self._client:
            self._client = None
            logger.info("Supabase desconectado.")

    async def get_pending_urls(self, limit: int = 50) -> list[PendingUrl]:
        """
        Obtiene URLs pendientes de envío.

        Args:
            limit: Máximo de URLs a recuperar por lote.

        Returns:
            Lista de PendingUrl ordenadas por ID ascendente.
        """
        if not self._client:
            logger.warning("get_pending_urls: Cliente no inicializado.")
            return []

        try:
            response = (
                self._client.table("url")
                .select("id, url, keyword, send_tg")
                .eq("send_tg", False)
                .order("id", desc=False)
                .limit(limit)
                .execute()
            )

            rows = response.data or []

            if rows:
                logger.debug("Recuperadas %d URLs pendientes.", len(rows))
            return [PendingUrl(**row) for row in rows]

        except Exception as exc:
            logger.error("Error obteniendo URLs pendientes: %s", exc)
            return []

    async def mark_as_sent(self, url_id: int) -> bool:
        """
        Marca una URL como enviada a Telegram.

        Args:
            url_id: ID de la URL en Supabase.

        Returns:
            True si se actualizó correctamente.
        """
        if not self._client:
            return False

        try:
            now_iso = datetime.now(timezone.utc).isoformat()

            response = (
                self._client.table("url")
                .update({
                    "send_tg": True,
                })
                .eq("id", url_id)
                .execute()
            )

            if response.data:
                logger.debug("URL id=%d marcada como enviada.", url_id)
                return True

            logger.warning("No se encontró URL id=%d para marcar.", url_id)
            return False

        except Exception as exc:
            logger.error("Error marcando URL id=%d como enviada: %s", url_id, exc)
            return False

    async def get_pending_count(self) -> int:
        """
        Retorna el número de URLs pendientes de envío.

        Returns:
            Cantidad de URLs con send_tg = false.
        """
        if not self._client:
            return 0

        try:
            response = (
                self._client.table("url")
                .select("id", count="exact")
                .eq("send_tg", False)
                .execute()
            )

            return response.count or 0

        except Exception as exc:
            logger.error("Error contando URLs pendientes: %s", exc)
            return 0