from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import async_session
from bot.keyboards import main_menu_kb
from bot.services.orders import get_or_create_user

router = Router()

WELCOME_TEXT = (
    "👋 Добро пожаловать!\n\n"
    "Здесь вы можете купить:\n"
    "⭐ Telegram Stars\n"
    "💎 Telegram Premium\n"
    "🎮 Донат в популярные игры\n\n"
    "Выберите раздел ниже 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session() as session:
        await get_or_create_user(
            session, message.from_user.id, message.from_user.username, message.from_user.full_name
        )
        await session.commit()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()
