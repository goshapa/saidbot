from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import back_to_menu_kb, main_menu_kb
from bot.services.notify import notify_admins
from bot.states import SupportFSM

router = Router()


@router.callback_query(F.data == "support")
async def ask_support_message(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportFSM.waiting_message)
    await callback.message.edit_text(
        "✍️ Опишите ваш вопрос одним сообщением — мы передадим его администратору.",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.message(SupportFSM.waiting_message)
async def forward_support_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = (
        f"🆘 Обращение в поддержку\n"
        f"От: @{message.from_user.username or message.from_user.id} (id {message.from_user.id})\n\n"
        f"{message.text}"
    )
    await notify_admins(message.bot, text)
    await message.answer("Спасибо! Ваше сообщение передано администратору.", reply_markup=main_menu_kb())
