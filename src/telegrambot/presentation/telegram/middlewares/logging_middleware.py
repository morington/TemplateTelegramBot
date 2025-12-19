import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src import Loggers

logger = structlog.getLogger(Loggers.logging_middleware.name)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging incoming Telegram events."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Intercepts all incoming updates and logs them."""
        with structlog.contextvars.bound_contextvars(_trace=uuid.uuid4().hex):
            log_params: dict[str, Any] = {}

            # Try to safely extract user/chat info
            user_id = getattr(event.event.from_user, "id", None)
            chat_id = None
            if isinstance(event.event, Message):
                chat_id = getattr(event.event.chat, "id", None)
            elif isinstance(event.event, CallbackQuery):
                chat_id = getattr(event.event.message.chat, "id", None)

            log_params.update(user_id=user_id, chat_id=chat_id)

            # Determine event type and log details
            if isinstance(event.event, Message):
                message_type, extra = self._extract_message_params(event.event)
                log_params.update(extra)
                await logger.ainfo(message_type, **log_params)

            elif isinstance(event.event, CallbackQuery):
                await logger.ainfo(
                    "Request `CallbackQuery`",
                    _data=event.event.data,
                    **log_params,
                )

            else:
                await logger.adebug("Unknown Request", _data=event.to_dict())

            # Execute the next handler
            result = await handler(event, data)

            # Detect unhandled responses
            if getattr(result, "name", None) == "UNHANDLED":
                await logger.awarning("Unhandled Request", **log_params)

            return result

    @staticmethod
    def _extract_message_params(event: Message) -> tuple[str, dict[str, Any]]:
        """Extracts message type and relevant attributes for logging."""
        handlers = {
            "text": lambda: ("Request `Message`", {"_message": event.text}),
            "audio": lambda: (
                "Request `Audio`",
                {
                    "file_id": event.audio.file_id,
                    "file_unique_id": event.audio.file_unique_id,
                },
            ),
            "sticker": lambda: (
                "Request `Sticker`",
                {
                    "file_id": event.sticker.file_id,
                    "file_unique_id": event.sticker.file_unique_id,
                },
            ),
            "animation": lambda: (
                "Request `Animation`",
                {
                    "file_id": event.animation.file_id,
                    "file_unique_id": event.animation.file_unique_id,
                },
            ),
            "photo": lambda: (
                "Request `Photo`",
                {
                    "file_id": event.photo[-1].file_id,
                    "file_unique_id": event.photo[-1].file_unique_id,
                },
            ),
            "poll": lambda: (
                "Request `Poll`",
                {
                    "poll_id": event.poll.id,
                    "question": event.poll.question,
                    "options": [option.text for option in event.poll.options],
                },
            ),
            "video": lambda: (
                "Request `Video`",
                {
                    "file_id": event.video.file_id,
                    "file_unique_id": event.video.file_unique_id,
                },
            ),
            "document": lambda: (
                "Request `Document`",
                {
                    "file_name": event.document.file_name,
                    "file_id": event.document.file_id,
                    "file_unique_id": event.document.file_unique_id,
                },
            ),
        }

        for attr, handler in handlers.items():
            if getattr(event, attr, None):
                return handler()

        return "Unknown Request", {"raw": event.model_dump()}
