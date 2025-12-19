from dishka import Provider, Scope


class RepositoryProvider(Provider):
    """DI provider for all.ftl repository classes."""

    scope = Scope.REQUEST
