from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db import async_session
from app.models import Order, OrderStatus, Product
from bot.handlers.catalog import _create_pending_order
from bot.keyboards import back_to_menu_kb, main_menu_kb
from bot.services.notify import notify_admins
from bot.services.orders import get_active_card, order_summary_text
from bot.states import OrderFSM

router = Router()


@router.message(OrderFSM.entering_recipient)
async def receive_recipient(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    product_id = data.get("product_id")

    async with async_session() as session:
        product = await session.get(Product, product_id)

    if product is None:
        await message.answer("Товар больше не доступен.", reply_markup=main_menu_kb())
        await state.clear()
        return

    recipient_info = message.text.strip()
    if not recipient_info:
        await message.answer("Пожалуйста, отправьте текстом.")
        return

    class _FakeCallback:
        def __init__(self, message: Message):
            self.message = message
            self.from_user = message.from_user

        async def answer(self, *args, **kwargs):
            return None

    await _create_pending_order(_FakeCallback(message), state, product, recipient_info)


@router.callback_query(OrderFSM.confirming, F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")

    async with async_session() as session:
        order = await session.get(Order, order_id)
        card = await get_active_card(session)

    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    if card is None:
        await callback.message.edit_text(
            "⚠️ Оплата временно недоступна: реквизиты не настроены. Обратитесь в поддержку.",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    text = (
        f"💳 Оплатите заказ №{order.id} на сумму "
        f"{order.total_price:,.0f} {settings.CURRENCY}".replace(",", " ") + "\n\n"
        f"Банк: {card.bank_name}\n"
        f"Номер карты: {card.card_number}\n"
        f"Получатель: {card.holder_name}\n\n"
        "После оплаты пришлите сюда скриншот/фото чека одним сообщением."
    )
    await state.set_state(OrderFSM.waiting_receipt)
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(OrderFSM.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")

    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await message.answer("Заказ не найден.", reply_markup=main_menu_kb())
            await state.clear()
            return

        order.receipt_file_id = message.photo[-1].file_id
        order.status = OrderStatus.AWAITING_REVIEW.value
        product = await session.get(Product, order.product_id)
        summary = order_summary_text(order, product)
        await session.commit()

    await state.clear()
    await message.answer(
        "✅ Чек получен! Заказ отправлен администратору на проверку. "
        "Мы уведомим вас, как только оплата будет подтверждена.",
        reply_markup=main_menu_kb(),
    )

    from bot.keyboards import admin_order_kb

    admin_text = (
        f"🆕 Новый заказ на проверку\n\n{summary}\n"
        f"Покупатель: @{message.from_user.username or message.from_user.id}"
    )
    await notify_admins(
        message.bot,
        admin_text,
        reply_markup=admin_order_kb(order.id),
        photo_file_id=order.receipt_file_id,
    )


@router.message(OrderFSM.waiting_receipt)
async def receipt_wrong_type(message: Message) -> None:
    await message.answer("Пожалуйста, пришлите именно фото/скриншот чека об оплате.")
