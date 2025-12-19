import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from aiohttp import web

if TYPE_CHECKING:
    from aiogram.types import WebhookInfo
    from fluentogram import TranslatorRunner

from src import Configuration, Loggers
from src.telegrambot.infrastructure.i18n_translator import create_translator_runner
from src.telegrambot.presentation.telegram.dialogs import commands
from src.telegrambot.presentation.telegram.dialogs.flow import default
from src.telegrambot.presentation.telegram.middlewares.logging_middleware import LoggingMiddleware

logger = structlog.getLogger(Loggers.main.name)


class TelegramBot:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration

        i18n: TranslatorRunner = create_translator_runner(locale_dir=Path("locales"))

        self.web_app = web.Application()
        self.web_app.router.add_get("/health", self.handle_health_check)

        self.dispatcher = Dispatcher(i18n=i18n)
        self.dispatcher.workflow_data.update({"i18n": i18n})
        self.bot = Bot(
            token=self.configuration.telegram.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
        )

        self.dispatcher.update.middleware(LoggingMiddleware())

        self.dispatcher.include_routers(commands.router)

        self.dispatcher.include_routers(
            default.default_dialog,
        )

        setup_dialogs(self.dispatcher)

    async def handle_health_check(self, request: web.Request) -> web.Response:
        """
        Обрабатывает запросы проверки состояния приложения (health check).
        Возвращает безопасную информацию о состоянии системы без раскрытия чувствительных данных.
        """
        return web.json_response({"status": "ok"})

    async def run(self) -> None:
        if self.configuration.is_development:
            await logger.ainfo("Launched...", mode="polling")
            await self.dispatcher.start_polling(self.bot)
        else:
            await logger.ainfo("Launched...", mode="webhook")

            webhook_url = f"{self.configuration.webhook.host}{self.configuration.webhook.path}"
            webhook_info: WebhookInfo = await self.bot.get_webhook_info()
            await logger.adebug(
                "Webhook info", url=webhook_info.url, has_custom_certificate=webhook_info.has_custom_certificate
            )

            if webhook_info.url != webhook_url:
                await self.bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=self.dp.resolve_used_update_types(),
                    drop_pending_updates=False,
                )
                await logger.ainfo("Webhook successfully set", url=webhook_url)
            else:
                await logger.ainfo("Webhook already configured", url=webhook_url)

            runner = web.AppRunner(self.web_app)
            await runner.setup()

            host: str = self.configuration.webapp.host
            port: int = self.configuration.webapp.port
            web_server = web.TCPSite(runner, host=host, port=port)
            logger.info("Starting webhook server", host=host, port=port)

            await web_server.start()

            try:
                await asyncio.Event().wait()
            finally:
                await runner.cleanup()

    async def close(self) -> None: ...
