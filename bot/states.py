from aiogram.fsm.state import State, StatesGroup


class OrderFSM(StatesGroup):
    entering_recipient = State()
    confirming = State()
    waiting_receipt = State()


class SupportFSM(StatesGroup):
    waiting_message = State()
