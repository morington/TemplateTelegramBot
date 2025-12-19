import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src import Loggers
from src.telegrambot.presentation.telegram.dialogs.flow.default.states import DefaultSG

logger = structlog.getLogger(Loggers.main.name)
router = Router(name=__name__)


@router.message(CommandStart())
async def start_command(message: Message, dialog_manager: DialogManager, **kwargs) -> None:
    await dialog_manager.start(DefaultSG.main, mode=StartMode.RESET_STACK)
