from enum import StrEnum

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TelegramSettings(BaseModel):
    token: str = Field(...)


class WebhookSetting(BaseSettings):
    host: str = Field(...)
    path: str = Field(...)


class WebappSetting(BaseSettings):
    host: str = Field(...)
    port: int = Field(...)


class PostgresqlSetting(BaseModel):
    """
    PostgreSQL connection settings.

    Used to form a database connection string.
    """

    host: str | None = Field(default="localhost", description="PostgreSQL host", examples=["localhost", "postgres"])
    port: int | None = Field(default=5432, description="Port PostgreSQL", examples=[5432], ge=1, le=65535)
    user: str | None = Field(default="postgres", description="Database user name", examples=["postgres"])
    password: str | None = Field(default=None, description="Database user password", repr=False)
    db: str | None = Field(default=None, description="Database Name", examples=["app_db"])

    def url(self, schema: str) -> str:
        """
        Generates a connection string to PostgreSQL.

        Attributes:
            schema: The wiring diagram (for example: postgresql, postgresql+asyncpg).

        Returns:
            Database connection string.

        Raises:
            ValueError: If the required connection parameters are not specified.
        """
        if not all([self.host, self.port, self.user, self.password, self.db]):
            raise ValueError("PostgreSQL settings are incomplete")
        return f"{schema}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")
    environment: Environment = Field(default=Environment.DEVELOPMENT, alias="ENV")

    telegram: TelegramSettings
    webhook: WebhookSetting
    webapp: WebappSetting
    postgresql: PostgresqlSetting

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING
