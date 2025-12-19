from collections.abc import Iterable
from pathlib import Path

from fluentogram import TranslatorHub, TranslatorRunner
from fluentogram.storage.file import FileStorage


def _discover_locales(base: Path) -> list[str]:
    """
    Возвращает список локалей по структуре каталогов в base/<locale>/LC_MESSAGES/*.ftl

    Returns:
        list[str]: список кодов локалей (например, ["ru", "en"])

    """
    result: list[str] = []
    for loc_dir in base.iterdir():
        if not loc_dir.is_dir():
            continue
        if (loc_dir / "LC_MESSAGES").exists():
            result.append(loc_dir.name)
    return sorted(result)


def _build_locales_map(locales: Iterable[str], fallback: str) -> dict[str, tuple[str, ...]]:
    """
    Строит карту локалей с откатами: сначала текущая, потом fallback.

    Args:
        locales: набор доступных локалей (например, ["ru", "en"])
        fallback: корневая локаль, в которую откатываемся при отсутствии ключа

    Returns:
        dict[str, tuple[str, ...]]: карта для TranslatorHub

    """
    locales_map: dict[str, tuple[str, ...]] = {}
    for loc in locales:
        if loc == fallback:
            locales_map[loc] = (loc,)
        else:
            locales_map[loc] = (loc, fallback)
    return locales_map


def create_translator_hub(locale_dir: Path, *, default_locale: str = "ru") -> TranslatorHub:
    """
    Создает TranslatorHub, автоматически подхватывая все .ftl в locales/<locale>/LC_MESSAGES/.

    Returns:
        TranslatorHub

    """
    available: list[str] = _discover_locales(locale_dir)
    if default_locale not in available:
        # Не бросаем исключение, а просто добавляем как fallback — чтобы не упасть в рантайме.
        available.append(default_locale)

    locales_map = _build_locales_map(available, fallback=default_locale)

    storage = FileStorage(str(locale_dir / "{locale}"))

    return TranslatorHub(
        locales_map=locales_map,
        storage=storage,
        root_locale=default_locale,
    )


def create_translator_runner(
    locale_dir: Path, *, default_locale: str = "ru", fallback_lang: str | None = None
) -> TranslatorRunner:
    """
    Создает TranslatorRunner для выбранной локали на основе уже сконфигурированного TranslatorHub.

    Args:
        locale_dir: корень каталога с локалями (locales/)
        default_locale: язык приложения на этот запуск (например, 'ru' или 'en')
        fallback_lang: необязательная корневая локаль для отката

    Returns:
        TranslatorRunner

    """
    hub = create_translator_hub(locale_dir, default_locale=fallback_lang or default_locale)
    return hub.get_translator_by_locale(default_locale)
