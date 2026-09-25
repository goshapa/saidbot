from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import settings
from app.models import PRODUCT_TYPE_LABELS, Category, Order, Product

MAIN_MENU_BUTTONS = [
    ("⭐ Telegram Stars", "cat_type:stars"),
    ("💎 Telegram Premium", "cat_type:premium"),
    ("🎮 Донат в игры", "cat_type:game"),
]


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = []
    if settings.WEBAPP_URL:
        rows.append(
            [InlineKeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=settings.WEBAPP_URL))]
        )
    rows += [[InlineKeyboardButton(text=text, callback_data=cb)] for text, cb in MAIN_MENU_BUTTONS]
    rows.append([InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")])
    rows.append([InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_menu")]]
    )


def categories_kb(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.title, callback_data=f"category:{c.id}")] for c in categories
    ]
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_kb(products: list[Product], category_type: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p.title} — {p.price:,.0f} {settings.CURRENCY}".replace(",", " "),
                callback_data=f"product:{p.id}",
            )
        ]
        for p in products
    ]
    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_type:{category_type}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_order_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")],
        ]
    )


def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"adm_approve:{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_reject:{order_id}"),
            ],
            [InlineKeyboardButton(text="🎉 Отметить выполненным", callback_data=f"adm_complete:{order_id}")],
        ]
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True, one_time_keyboard=True
    )
