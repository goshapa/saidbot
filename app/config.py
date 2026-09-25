import os

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> list[int]:
    ids = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            ids.append(int(chunk))
    return ids


def _parse_int(raw: str) -> int:
    raw = raw.strip()
    return int(raw) if raw.isdigit() else 0


def _normalize_database_url(raw: str) -> str:
    """Railway (and most hosts) hand out a plain postgres://... URL meant for
    sync drivers. Rewrite it to use the async driver our engine needs, so a
    copy-pasted DATABASE_URL just works without the user editing it."""
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://"):
        raw = "postgresql+asyncpg://" + raw[len("postgresql://"):]
    return raw


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    ADMIN_CHAT_ID: int = _parse_int(os.getenv("ADMIN_CHAT_ID", "0"))

    DATABASE_URL: str = _normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/saidbot.db")
    )
    CURRENCY: str = os.getenv("CURRENCY", "UZS")

    ADMIN_PANEL_USERNAME: str = os.getenv("ADMIN_PANEL_USERNAME", "admin")
    ADMIN_PANEL_PASSWORD: str = os.getenv("ADMIN_PANEL_PASSWORD", "change_me")
    ADMIN_PANEL_SECRET: str = os.getenv("ADMIN_PANEL_SECRET", "change_me_secret")

    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")


settings = Settings()
