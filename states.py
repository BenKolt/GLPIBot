from aiogram.fsm.state import State, StatesGroup

class NewTicket(StatesGroup):
    title = State()
    description = State()
