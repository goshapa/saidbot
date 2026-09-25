from aiogram import Bot

from app.config import settings
from app.models import ORDER_STATUS_LABELS, Order


async def notify_admins(bot: Bot, text: str, reply_markup=None, photo_file_id: str | None = None) -> None:
    targets = set(settings.ADMIN_IDS)
    if settings.ADMIN_CHAT_ID:
        targets.add(settings.ADMIN_CHAT_ID)

    for chat_id in targets:
        try:
            if photo_file_id:
                await bot.send_photo(chat_id, photo_file_id, caption=text, reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id, text, reply_markup=reply_markup)
        except Exception:
            continue


async def notify_user_status(bot: Bot, order: Order) -> None:
    status_label = ORDER_STATUS_LABELS.get(order.status, order.status)
    text = f"Статус заказа №{order.id} изменён: {status_label}"
    if order.admin_comment:
        text += f"\nКомментарий: {order.admin_comment}"
    try:
        await bot.send_message(order.user.tg_id, text)
    except Exception:
        pass
