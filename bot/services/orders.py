from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Order, PaymentCard, Product, User


async def get_or_create_user(session: AsyncSession, tg_id: int, username: str | None, full_name: str | None) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(tg_id=tg_id, username=username, full_name=full_name)
        session.add(user)
        await session.flush()
    else:
        user.username = username
        user.full_name = full_name
    return user


async def get_active_card(session: AsyncSession) -> PaymentCard | None:
    result = await session.execute(
        select(PaymentCard).where(PaymentCard.is_active.is_(True)).order_by(PaymentCard.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


def order_summary_text(order: Order, product: Product) -> str:
    lines = [
        f"🧾 Заказ №{order.id}",
        f"Товар: {product.title}",
        f"Сумма к оплате: {order.total_price:,.0f} {settings.CURRENCY}".replace(",", " "),
    ]
    if order.recipient_info:
        lines.append(f"Получатель: {order.recipient_info}")
    return "\n".join(lines)
