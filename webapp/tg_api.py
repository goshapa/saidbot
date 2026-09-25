import json

import httpx

from app.config import settings
from app.models import Order

API_BASE = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"


def _admin_order_keyboard(order_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить оплату", "callback_data": f"adm_approve:{order_id}"},
                {"text": "❌ Отклонить", "callback_data": f"adm_reject:{order_id}"},
            ],
            [{"text": "🎉 Отметить выполненным", "callback_data": f"adm_complete:{order_id}"}],
        ]
    }


async def send_receipt_to_admins(order: Order, photo_bytes: bytes) -> str | None:
    targets = set(settings.ADMIN_IDS)
    if settings.ADMIN_CHAT_ID:
        targets.add(settings.ADMIN_CHAT_ID)

    price_text = f"{order.total_price:,.0f} {settings.CURRENCY}".replace(",", " ")
    text = (
        f"🆕 Новый заказ на проверку (из мини-аппа)\n\n"
        f"Заказ №{order.id}\n"
        f"Товар: {order.product.title}\n"
        f"Сумма: {price_text}\n"
    )
    if order.recipient_info:
        text += f"Получатель: {order.recipient_info}\n"
    text += f"Покупатель: @{order.user.username or order.user.tg_id}"

    keyboard = json.dumps(_admin_order_keyboard(order.id))
    file_id: str | None = None

    async with httpx.AsyncClient(timeout=20) as client:
        for chat_id in targets:
            files = {"photo": ("receipt.jpg", photo_bytes, "image/jpeg")}
            data = {"chat_id": str(chat_id), "caption": text, "reply_markup": keyboard}
            try:
                resp = await client.post(f"{API_BASE}/sendPhoto", data=data, files=files)
                result = resp.json()
            except Exception:
                continue
            if result.get("ok") and file_id is None:
                photos = result["result"].get("photo") or []
                if photos:
                    file_id = photos[-1]["file_id"]

    return file_id


async def notify_user(tg_id: int, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(f"{API_BASE}/sendMessage", json={"chat_id": tg_id, "text": text})
        except Exception:
            pass
