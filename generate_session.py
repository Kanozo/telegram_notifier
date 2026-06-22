"""
generate_session.py
Script para generar una SESSION_STRING de Telethon.

Uso:
  python generate_session.py

Solicita:
  - API_ID y API_HASH de my.telegram.org
  - Número de teléfono (con código de país)
  - Código de verificación de Telegram
  - Contraseña 2FA (si está activada)

Genera:
  - SESSION_STRING para pegar en .env
"""

from __future__ import annotations

import asyncio
import socks

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    print("=" * 50)
    print("Generador de SESSION_STRING para Telegram")
    print("=" * 50)
    print()

    api_id = int(input("API ID: "))
    api_hash = input("API Hash: ")
    PROXY = (socks.HTTP, '192.168.30.120', 3128, True)
    session = StringSession()
    async with TelegramClient(session, api_id, api_hash, proxy=PROXY) as client:
        print("\nConectando a Telegram...")

        print("\n" + "=" * 50)
        print("✅ SESSION_STRING generada:")
        print("=" * 50)
        print(session.save())
        print("=" * 50)
        print("\nCopia esta string en tu archivo .env como SESSION_STRING")


if __name__ == "__main__":
    asyncio.run(main())