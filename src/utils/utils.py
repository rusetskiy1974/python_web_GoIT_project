import asyncio
import datetime

from src.routes.auth import blacklisted_tokens


def cleanup_blacklist():
    blacklisted_tokens.clear()


async def periodic_clean_blacklist(time: int = 60):
    # Запускається кожні 60 хвилин
    while True:
        cleanup_blacklist()
        await asyncio.sleep(60 * time)

