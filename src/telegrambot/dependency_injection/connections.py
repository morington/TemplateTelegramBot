import time
from collections.abc import AsyncIterable
from typing import Any

import structlog
from dishka import Provider, Scope, provide
from sqlalchemy import Connection, event, text
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src import Configuration, Loggers

logger = structlog.getLogger(Loggers.main.name)


async def _check_read_write(engine: AsyncEngine) -> bool:
    """
    Проверяет, доступна ли база данных в режиме read-write.

    Args:
        engine: Асинхронный движок SQLAlchemy

    Returns:
        bool: True, если база данных доступна в режиме read-write, иначе False
    """
    async with engine.connect() as conn:
        result = await conn.execute(text("SHOW transaction_read_only"))
        return result.scalar() == "off"


def before_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool,  # noqa: FBT001
) -> None:
    """
    Ставит таймер перед выполнением SQL-запроса.

    Args:
        conn: Объект соединения
        cursor: Курсор базы данных
        statement: SQL-запрос
        parameters: Параметры запроса
        context: Контекст выполнения
        executemany: Флаг множественного выполнения

    Returns:
        None
    """
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


def after_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool,  # noqa: FBT001
) -> None:
    """
    Считает длительность выполнения SQL-запроса и логирует её.

    Args:
        conn: Объект соединения
        cursor: Курсор базы данных
        statement: SQL-запрос
        parameters: Параметры запроса
        context: Контекст выполнения
        executemany: Флаг множественного выполнения

    Returns:
        None
    """
    start_stack = conn.info.get("query_start_time")
    if not start_stack:
        return
    duration = time.perf_counter() - start_stack.pop()
    logger.debug("SQL Query complete", duration=round(duration, 6))


async def _create_engine(url: str | URL, ssl: str) -> AsyncEngine | None:
    """
    Создает асинхронный движок для работы с PostgreSQL.

    Args:
        url: Строка подключения или объект URL
        ssl: Настройки SSL-соединения

    Returns:
        AsyncEngine | None: Движок в случае успешного подключения, иначе None
    """
    engine = create_async_engine(
        url,
        pool_size=10,
        max_overflow=5,
        pool_recycle=300,
        pool_pre_ping=True,
        pool_timeout=30,
        connect_args={"ssl": ssl},
    )
    event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
    event.listen(engine.sync_engine, "after_cursor_execute", after_cursor_execute)

    if await _check_read_write(engine):
        return engine

    await engine.dispose()
    return None


async def get_engine(url: str | URL, ssl: str = "disable") -> AsyncEngine:
    """
    Получает асинхронный движок для работы с PostgreSQL.

    Args:
        url: Строка подключения или объект URL
        ssl: Настройки SSL-соединения

    Returns:
        AsyncEngine: Движок PostgreSQL

    Raises:
        ConnectionError: Если не удалось подключиться к read-write узлу PostgreSQL
    """
    engine = await _create_engine(url, ssl)
    if engine:
        return engine

    raise ConnectionError("Could not connect to any read-write PostgreSQL host")


class ConnectionProvider(Provider):
    """DI-провайдер соединений с брокером сообщений и базой данных"""

    scope = Scope.APP

    @provide
    async def engine(self, config: Configuration) -> AsyncIterable[AsyncEngine]:
        """
        Создает и возвращает асинхронный движок для работы с базой данных.

        Args:
            config: Конфигурация приложения

        Yields:
            AsyncIterable[AsyncEngine]: Асинхронный движок SQLAlchemy
        """
        await logger.adebug("Create PostgreSQL URL", url=config.postgresql_url)

        engine = await get_engine(config.postgresql_url)
        yield engine
        await engine.dispose()

    @provide
    async def session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        """
        Создает фабрику асинхронных сессий для работы с базой данных.

        Args:
            engine: Асинхронный движок SQLAlchemy

        Returns:
            async_sessionmaker[AsyncSession]: Фабрика сессий
        """
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        """
        Создает асинхронную сессию для работы с базой данных.

        Args:
            session_factory: Фабрика асинхронных сессий

        Yields:
            AsyncIterable[AsyncSession]: Экземпляр асинхронной сессии
        """
        async with session_factory() as session:
            yield session
