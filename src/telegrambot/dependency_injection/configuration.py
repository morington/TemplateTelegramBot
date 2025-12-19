from dishka import Provider, Scope, from_context

from src import Configuration


class ConfigurationProvider(Provider):
    """Provides application-wide configuration settings."""

    config = from_context(provides=Configuration, scope=Scope.APP)
