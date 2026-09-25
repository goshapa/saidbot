from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db import async_session
from app.models import PRODUCT_TYPE_LABELS, Category, Product
from bot.keyboards import categories_kb, confirm_order_kb, products_kb
from bot.states import OrderFSM

router = Router()


@router.callback_query(F.data.startswith("cat_type:"))
async def show_categories(callback: CallbackQuery, state: FSMContext) -> None:
    category_type = callback.data.split(":", 1)[1]
    async with async_session() as session:
        result = await session.execute(
            select(Category)
            .where(Category.type == category_type, Category.is_active.is_(True))
            .order_by(Category.sort_order)
        )
        categories = list(result.scalars())

    if not categories:
        await callback.answer("Пока нет доступных товаров в этом разделе.", show_alert=True)
        return

    if len(categories) == 1:
        await _show_products(callback, categories[0])
        return

    label = PRODUCT_TYPE_LABELS.get(category_type, "Каталог")
    await callback.message.edit_text(f"{label}\n\nВыберите категорию:", reply_markup=categories_kb(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_products_by_category(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        category = await session.get(Category, category_id)
        if category is None:
            await callback.answer("Категория не найдена", show_alert=True)
            return
        await _show_products(callback, category, session)


async def _show_products(callback: CallbackQuery, category: Category, session=None) -> None:
    own_session = session is None
    if own_session:
        session = async_session()
    try:
        result = await session.execute(
            select(Product)
            .where(Product.category_id == category.id, Product.is_active.is_(True))
            .order_by(Product.sort_order)
        )
        products = list(result.scalars())
    finally:
        if own_session:
            await session.close()

    if not products:
        await callback.answer("Пока нет доступных товаров в этой категории.", show_alert=True)
        return

    await callback.message.edit_text(
        f"{category.title}\n\nВыберите товар:",
        reply_markup=products_kb(products, category.type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        product = await session.get(Product, product_id)

    if product is None or not product.is_active:
        await callback.answer("Товар недоступен", show_alert=True)
        return

    await state.update_data(product_id=product.id)

    if product.requires_recipient:
        from bot.states import OrderFSM

        await state.set_state(OrderFSM.entering_recipient)
        await callback.message.edit_text(
            f"Вы выбрали: {product.title}\n"
            f"Цена: {product.price:,.0f}".replace(",", " ") + "\n\n"
            f"Введите {product.recipient_label.lower()}:"
        )
    else:
        await _create_pending_order(callback, state, product)
    await callback.answer()


async def _create_pending_order(callback, state, product, recipient_info: str | None = None):
    from app.models import Order
    from bot.services.orders import get_or_create_user, order_summary_text

    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id, callback.from_user.username, callback.from_user.full_name
        )
        order = Order(
            user_id=user.id,
            product_id=product.id,
            total_price=product.price,
            recipient_info=recipient_info,
        )
        session.add(order)
        await session.flush()
        text = order_summary_text(order, product)
        order_id = order.id
        await session.commit()

    await state.update_data(order_id=order_id)
    await state.set_state(OrderFSM.confirming)
    await callback.message.answer(
        f"{text}\n\nПроверьте данные и подтвердите заказ.",
        reply_markup=confirm_order_kb(),
    )
