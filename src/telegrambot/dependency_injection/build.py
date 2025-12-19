from typing import Any

from dishka import AsyncContainer, make_async_container
from dishka.provider import BaseProvider

from src.telegrambot.dependency_injection.configuration import ConfigurationProvider
from src.telegrambot.dependency_injection.connections import ConnectionProvider
from src.telegrambot.dependency_injection.repository import RepositoryProvider


def build_container(context: dict[Any, Any] | None = None, *providers: BaseProvider) -> AsyncContainer:
    """
    Сконфигурировать DI-контейнер приложения.

    Returns:
        AsyncContainer: готовый контейнер зависимостей.
    """
    container: AsyncContainer = make_async_container(
        ConfigurationProvider(), ConnectionProvider(), RepositoryProvider(), *providers, context=context
    )

    return container
