from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from src.telegrambot.presentation.telegram.dialogs.flow.default.states import DefaultSG


async def on_select_wrong_button(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager) -> None:
    await dialog_manager.switch_to(state=DefaultSG.wrong_button, show_mode=ShowMode.DELETE_AND_SEND)


async def on_select_right_button(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager) -> None:
    await dialog_manager.switch_to(state=DefaultSG.right_button, show_mode=ShowMode.DELETE_AND_SEND)
