from aiogram.fsm.state import State, StatesGroup


class DefaultSG(StatesGroup):
    main = State()
    wrong_button = State()
    right_button = State()
