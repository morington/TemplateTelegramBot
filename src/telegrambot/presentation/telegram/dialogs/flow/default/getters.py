from aiogram_dialog import DialogManager


async def getter_welcome_message(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"user_fullname": dialog_manager.event.from_user.full_name}
