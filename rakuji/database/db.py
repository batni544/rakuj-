"""
Veritabanı katmanı — asyncpg PostgreSQL connection pool
"""
import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    await _create_tables()


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Veritabanı başlatılmadı! init_db() çağır.")
    return _pool


async def _create_tables() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id        BIGINT PRIMARY KEY,
            log_channel_id  BIGINT,
            panic_mode      BOOLEAN DEFAULT FALSE,
            raid_threshold  INT     DEFAULT 5,
            raid_window_sec INT     DEFAULT 10,
            whitelist       BIGINT[] DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS anti_nuke_config (
            guild_id        BIGINT PRIMARY KEY,
            channel_delete  INT DEFAULT 3,
            role_delete     INT DEFAULT 3,
            ban_count       INT DEFAULT 5,
            kick_count      INT DEFAULT 5,
            webhook_delete  INT DEFAULT 2,
            window_sec      INT DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            guild_id        BIGINT NOT NULL,
            user_id         BIGINT NOT NULL,
            warns           INT    DEFAULT 0,
            last_warn_at    TIMESTAMPTZ,
            last_warn_reason TEXT,
            UNIQUE(guild_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS quarantined (
            id              SERIAL PRIMARY KEY,
            guild_id        BIGINT NOT NULL,
            user_id         BIGINT NOT NULL,
            reason          TEXT,
            quarantined_at  TIMESTAMPTZ DEFAULT NOW(),
            active          BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE IF NOT EXISTS action_log (
            id              SERIAL PRIMARY KEY,
            guild_id        BIGINT NOT NULL,
            action_type     TEXT   NOT NULL,
            target_id       BIGINT,
            executor_id     BIGINT,
            reason          TEXT,
            extra           TEXT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        );
        """)
