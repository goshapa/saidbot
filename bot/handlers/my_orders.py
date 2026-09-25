from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import async_session
from app.models import ORDER_STATUS_LABELS, Order, User
from bot.keyboards import back_to_menu_kb

router = Router()


@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery) -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        orders = []
        if user:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.product))
                .where(Order.user_id == user.id)
                .order_by(Order.created_at.desc())
                .limit(10)
            )
            orders = list(result.scalars())

    if not orders:
        await callback.message.edit_text("У вас пока нет заказов.", reply_markup=back_to_menu_kb())
        await callback.answer()
        return

    lines = ["📦 Ваши последние заказы:\n"]
    for order in orders:
        status = ORDER_STATUS_LABELS.get(order.status, order.status)
        price = f"{order.total_price:,.0f} {settings.CURRENCY}".replace(",", " ")
        lines.append(f"№{order.id} · {order.product.title} · {price} · {status}")

    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_menu_kb())
    await callback.answer()
