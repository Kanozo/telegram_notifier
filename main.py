"""
main.py
Servicio de notificación: lee URLs de Supabase y las envía a Telegram.

Flujo:
  1. Conectar a Supabase
  2. Conectar a Telegram vía StringSession
  3. Bucle infinito:
     a. Obtener URLs con send_tg = false
     b. Enviar cada URL al grupo de Telegram
     c. Marcar como enviada en Supabase
     d. Esperar intervalo configurable
  4. Manejar reconexiones ante errores transitorios

Ejecución:
  python main.py

Variables de entorno (.env):
  SUPABASE_URL, SUPABASE_KEY
  API_ID, API_HASH, SESSION_STRING, GROUP_TARGET
  SEND_INTERVAL_SECONDS (opcional, default 120)
  MESSAGE_DELAY_SECONDS (opcional, default 3)
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone

from config import settings
from supabase_client import SupabaseUrlReader
from telegram_notifier import TelegramNotifier

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("telegram_notifier")

# Silenciar logs de terceros
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)


class TelegramNotifierService:
    """
    Servicio principal que orquesta la lectura de URLs y envío a Telegram.

    Args:
        url_reader:     Cliente de Supabase para leer URLs.
        telegram_bot:   Cliente de Telegram para enviar mensajes.
        interval:       Segundos entre ciclos de envío.
        message_delay:  Segundos entre mensajes individuales.
    """

    def __init__(
        self,
        url_reader: SupabaseUrlReader,
        telegram_bot: TelegramNotifier,
        interval: int = 120,
        message_delay: float = 3.0,
    ) -> None:
        self._url_reader = url_reader
        self._telegram = telegram_bot
        self._interval = interval
        self._message_delay = message_delay
        self._running = False

    async def _process_batch(self) -> tuple[int, int]:
        """
        Procesa un lote de URLs pendientes.

        Returns:
            Tupla (enviadas, fallidas).
        """
        sent_count = 0
        failed_count = 0

        # Obtener URLs pendientes
        pending = await self._url_reader.get_pending_urls(limit=50)

        if not pending:
            return 0, 0

        logger.info("Procesando %d URLs pendientes...", len(pending))

        for item in pending:
            if not self._running:
                break

            # Enviar
            success = await self._telegram.send_message(item.url)

            if success:
                # Marcar como enviada en Supabase
                marked = await self._url_reader.mark_as_sent(item.id)
                if marked:
                    sent_count += 1
                    logger.info("✓ Enviada: %s", item.url)
                else:
                    # Se envió a Telegram pero no se pudo marcar en DB
                    logger.warning(
                        "⚠ Enviada a Telegram pero no marcada en DB: %s",
                        item.url[:60],
                    )
                    sent_count += 1  # Contar como enviada igual
            else:
                failed_count += 1
                logger.warning("✗ Falló envío: %s", item.url[:60])

            # Delay entre mensajes para evitar flood
            if self._message_delay > 0:
                await asyncio.sleep(self._message_delay)

        return sent_count, failed_count

    async def run(self) -> None:
        """
        Bucle principal del servicio.

        Se ejecuta hasta que recibe SIGINT o SIGTERM.
        """
        self._running = True

        # Manejar señales de parada
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.stop)

        logger.info("=" * 50)
        logger.info("Servicio de notificación Telegram iniciado")
        logger.info("Intervalo: %ds | Delay mensajes: %.1fs", self._interval, self._message_delay)
        logger.info("Grupo destino: %d", settings.GROUP_TARGET)
        logger.info("=" * 50)

        try:
            while self._running:
                cycle_start = datetime.now(timezone.utc)

                try:
                    sent, failed = await self._process_batch()

                    if sent > 0 or failed > 0:
                        logger.info(
                            "Ciclo completado: %d enviadas, %d fallidas.",
                            sent, failed,
                        )

                    # Mostrar contador de pendientes cada 10 ciclos
                    pending_count = await self._url_reader.get_pending_count()
                    if pending_count > 0:
                        logger.info("URLs pendientes restantes: %d", pending_count)

                except Exception as exc:
                    logger.error("Error en ciclo de procesamiento: %s", exc, exc_info=True)
                    # Continuar con el siguiente ciclo

                # Esperar hasta el próximo ciclo
                if self._running:
                    logger.debug("Esperando %ds hasta el próximo ciclo...", self._interval)
                    await asyncio.sleep(self._interval)

        except asyncio.CancelledError:
            logger.info("Servicio cancelado.")
        finally:
            logger.info("Servicio de notificación detenido.")

    def stop(self) -> None:
        """Señal de parada graceful."""
        logger.info("Señal de parada recibida. Finalizando ciclo actual...")
        self._running = False


async def main() -> None:
    """Punto de entrada principal."""

    # ── Validar configuración ─────────────────────────────────────────────
    if not settings.is_configured:
        logger.error(
            "Faltan variables de entorno. Copia .env.example a .env "
            "y completa los valores."
        )
        sys.exit(1)

    logger.info("Configuración: %s", settings)

    # ── Inicializar clientes ──────────────────────────────────────────────
    url_reader = SupabaseUrlReader()
    telegram_bot = TelegramNotifier(
        bot_token=settings.BOT_TOKEN,
        group_target=settings.GROUP_TARGET,
    )

    try:
        # Conectar a Supabase
        await url_reader.connect()

        # Conectar a Telegram (context manager para auto-disconnect)
        async with telegram_bot as bot:
            # Iniciar servicio
            service = TelegramNotifierService(
                url_reader=url_reader,
                telegram_bot=bot,
                interval=settings.SEND_INTERVAL_SECONDS,
                message_delay=settings.MESSAGE_DELAY_SECONDS,
            )
            await service.run()

    except RuntimeError as exc:
        logger.error("Error de configuración: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Error fatal: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        await url_reader.disconnect()
        logger.info("Servicio finalizado.")


if __name__ == "__main__":
    asyncio.run(main())