import asyncio
import logging
import os
from pathlib import Path

import asyncpg

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CONNECT_RETRIES = 10
CONNECT_RETRY_DELAY = 3

log = logging.getLogger("trolley.db")


async def create_pool() -> asyncpg.Pool:
    dsn = os.environ["DATABASE_URL"]
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            pool = await asyncpg.create_pool(dsn)
            break
        except (OSError, asyncpg.PostgresError):
            if attempt == CONNECT_RETRIES:
                raise
            log.info("database not ready yet (attempt %d/%d), retrying...", attempt, CONNECT_RETRIES)
            await asyncio.sleep(CONNECT_RETRY_DELAY)

    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_PATH.read_text())
    return pool
