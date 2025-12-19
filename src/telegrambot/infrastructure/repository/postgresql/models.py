from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeMeta, Mapped, declarative_base, mapped_column

Base: DeclarativeMeta = declarative_base()


class SQLAlchemyMixin:
    """
    A common mixin for SQLAlchemy models.

    Attributes:
        id: The unique identifier of the record (PK).
        created_at: Record creation time (automatic).
        updated_at: The time the record was last updated (automatic).
    """

    __table__: ClassVar[Any] = None
    __tablename__: ClassVar[str | None] = None

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __str__(self) -> str:
        """Returns a readable table name or class name."""
        return self.__tablename__ or self.__class__.__name__.lower()

    def __repr__(self) -> str:
        """Returns a service view of the instance."""
        table = self.__tablename__ or self.__class__.__name__
        return f"{table} ID: {getattr(self, 'id', None)}"

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes an object into a dictionary with value conversion
        into JSON-friendly structures.

        Returns:
            dict[str, Any]: Dictionary "column -> meaning".
        """
        return {
            c.name: self._json_serial(getattr(self, c.name))
            for c in self.__table__.columns  # type: ignore[attr-defined]
        }

    def to_entity_dict(self) -> dict[str, Any]:
        """
        Returns a raw dictionary of column values without serialization.

        Returns:
            dict[str, Any]: Dictionary "column -> original meaning".
        """
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns  # type: ignore[attr-defined]
        }

    @staticmethod
    def _json_serial(obj: Any) -> Any:
        """
        Auxiliary serializer for JSON.

        Attributes:
            obj: Object to serialize.

        Returns:
            Any: Converted value for known types.
        """
        if isinstance(obj, datetime):
            return {
                "human_format": obj.strftime("%d.%m.%Y %H:%M:%S"),
                "iso": obj.isoformat(),
                "timestamp": obj.timestamp(),
            }
        return obj


class TelegramUserModel(Base, SQLAlchemyMixin):
    """
    Telegram attributes of the user.

    Stores only data received from the Telegram API.
    It does not contain business logic, balance and restrictions.

    Attributes:
        telegram_id: Unique identifier of the user in Telegram.
        username: Username of the user in Telegram (may not be present).
        first_name: Telegram username (may not be present).
        last_name: User's last name in Telegram (may not be present).
        language_code: User language code (ISO 639-1).
    """

    __tablename__ = "telegram_user"

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(8))
