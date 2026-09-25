import httpx

from app.config import settings

API_BASE = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"


async def send_message(chat_id: int, text: str) -> None:
    if not settings.BOT_TOKEN:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(f"{API_BASE}/sendMessage", json={"chat_id": chat_id, "text": text})
        except Exception:
            pass


async def get_file_bytes(file_id: str) -> tuple[bytes, str] | None:
    if not settings.BOT_TOKEN:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{API_BASE}/getFile", params={"file_id": file_id})
        data = resp.json()
        if not data.get("ok"):
            return None
        file_path = data["result"]["file_path"]
        file_resp = await client.get(
            f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
        )
        content_type = "image/jpeg" if file_path.endswith((".jpg", ".jpeg")) else "application/octet-stream"
        return file_resp.content, content_type
