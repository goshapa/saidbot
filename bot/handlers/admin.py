from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import async_session
from app.models import Order, OrderStatus
from bot.services.notify import notify_user_status
from sqlalchemy import select

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


async def _load_order(order_id: int) -> Order | None:
    async with async_session() as session:
        result = await session.execute(
            select(Order).options(selectinload(Order.user), selectinload(Order.product)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()


@router.callback_query(F.data.startswith("adm_approve:"))
async def admin_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        order.status = OrderStatus.APPROVED.value
        await session.commit()

    order = await _load_order(order_id)
    await notify_user_status(callback.bot, order)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ Оплата подтверждена"
    ) if callback.message.caption else await callback.message.edit_text(
        (callback.message.text or "") + "\n\n✅ Оплата подтверждена"
    )
    await callback.answer("Оплата подтверждена")


@router.callback_query(F.data.startswith("adm_reject:"))
async def admin_reject(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        order.status = OrderStatus.REJECTED.value
        order.admin_comment = "Оплата не подтверждена. Свяжитесь с поддержкой."
        await session.commit()

    order = await _load_order(order_id)
    await notify_user_status(callback.bot, order)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ Отклонён"
    ) if callback.message.caption else await callback.message.edit_text(
        (callback.message.text or "") + "\n\n❌ Отклонён"
    )
    await callback.answer("Заказ отклонён")


@router.callback_query(F.data.startswith("adm_complete:"))
async def admin_complete(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        order.status = OrderStatus.COMPLETED.value
        await session.commit()

    order = await _load_order(order_id)
    await notify_user_status(callback.bot, order)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n🎉 Выполнен"
    ) if callback.message.caption else await callback.message.edit_text(
        (callback.message.text or "") + "\n\n🎉 Выполнен"
    )
    await callback.answer("Заказ отмечен выполненным")
