import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base

if settings.DATABASE_URL.startswith("sqlite"):
    _db_path = settings.DATABASE_URL.split("///")[-1]
    if _db_path and _db_path != ":memory:":
        os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Lightweight, additive schema patches for columns added after the initial
# release. create_all() only creates missing tables, not missing columns on
# tables that already exist, so new nullable/defaulted columns are added here.
# TRUE/FALSE (not 0/1) so this runs unmodified on both SQLite and Postgres.
_COLUMN_MIGRATIONS = [
    "ALTER TABLE products ADD COLUMN is_variable BOOLEAN DEFAULT FALSE",
    "ALTER TABLE products ADD COLUMN unit_price FLOAT",
    "ALTER TABLE products ADD COLUMN min_quantity INTEGER DEFAULT 1",
    "ALTER TABLE products ADD COLUMN image_url VARCHAR(1024)",
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Each statement runs in its own transaction so a "column already
    # exists" failure on one doesn't poison the rest (matters on Postgres).
    for statement in _COLUMN_MIGRATIONS:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(statement))
        except Exception:
            pass
