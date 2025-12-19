from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column

from src.telegrambot.presentation.telegram.dialogs.flow.default.getters import getter_welcome_message
from src.telegrambot.presentation.telegram.dialogs.flow.default.handlers import (
    on_select_right_button,
    on_select_wrong_button,
)
from src.telegrambot.presentation.telegram.dialogs.flow.default.states import DefaultSG
from src.telegrambot.presentation.telegram.dialogs.widgets.i18n import I18NFormat

welcome_message_window = Window(
    I18NFormat(key="welcome"),
    Column(
        Button(
            text=I18NFormat(key="wrong_button"),
            id="btn_my_pipelines",
            on_click=on_select_wrong_button,
        ),
        Button(
            text=I18NFormat(key="right_button"),
            id="btn_quick_access",
            on_click=on_select_right_button,
        ),
    ),
    state=DefaultSG.main,
    getter=getter_welcome_message,
)


wrong_button_window = Window(
    I18NFormat(key="send_wrong_button"),
    Button(
        text=I18NFormat(key="right_button"),
        id="btn_quick_access",
        on_click=on_select_right_button,
    ),
    state=DefaultSG.wrong_button,
)


right_button_window = Window(
    I18NFormat(key="send_right_button"),
    state=DefaultSG.right_button,
)


default_dialog = Dialog(
    welcome_message_window,
    wrong_button_window,
    right_button_window,
)
