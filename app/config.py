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


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    ADMIN_CHAT_ID: int = _parse_int(os.getenv("ADMIN_CHAT_ID", "0"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/saidbot.db")
    CURRENCY: str = os.getenv("CURRENCY", "UZS")

    ADMIN_PANEL_USERNAME: str = os.getenv("ADMIN_PANEL_USERNAME", "admin")
    ADMIN_PANEL_PASSWORD: str = os.getenv("ADMIN_PANEL_PASSWORD", "change_me")
    ADMIN_PANEL_SECRET: str = os.getenv("ADMIN_PANEL_SECRET", "change_me_secret")


settings = Settings()
