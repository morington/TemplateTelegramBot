import asyncio

import structlog
from dishka import Provider, Scope, provide
from dishka.integrations.aiogram import AiogramProvider, setup_dishka

from src import Configuration, Loggers
from src.telegrambot.dependency_injection import build_container
from src.telegrambot.infrastructure.bootstrap import TelegramBot

logger = structlog.getLogger(Loggers.main.name)


class TelegramBotProvider(Provider):
    app = provide(TelegramBot, scope=Scope.APP)


async def main() -> None:
    config = Configuration()
    Loggers(developer_mode=config.is_development)

    container = build_container({Configuration: config}, AiogramProvider(), TelegramBotProvider())
    application = await container.get(TelegramBot)

    setup_dishka(container=container, router=application.dispatcher, auto_inject=True)

    try:
        await logger.ainfo("Starting application....")
        await application.run()
    finally:
        await logger.awarning("[!] Close application....")
        await application.close()
        application.dispatcher.shutdown.register(container.close)


if __name__ == "__main__":
    asyncio.run(main())
