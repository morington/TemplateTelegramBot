from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column

from src.telegrambot.presentation.telegram.dialogs.flow.default.getters import getter_welcome_message
from src.telegrambot.presentation.telegram.dialogs.flow.default.states import DefaultSG
from src.telegrambot.presentation.telegram.dialogs.widgets.i18n import I18NFormat

welcome_message_window = Window(
    I18NFormat(key="welcome"),
    Column(
        Button(
            text=I18NFormat(key="btn"),
            id="btn_my_pipelines",
            # on_click=,
        ),
        Button(
            text=I18NFormat(key="btn"),
            id="btn_quick_access",
            # on_click=,
        ),
    ),
    state=DefaultSG.main,
    getter=getter_welcome_message,
)


default_dialog = Dialog(
    welcome_message_window,
)
