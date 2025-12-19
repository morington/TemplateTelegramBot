import ast
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.text import Text

if TYPE_CHECKING:
    from fluentogram import TranslatorRunner


class I18NFormat(Text):
    def __init__(self, key: str, when: WhenCondition = None):
        super().__init__(when)
        self.key = key

    async def _render_text(self, data: dict, dialog_manager: DialogManager) -> str:
        i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
        value = i18n.get(self.key, **data)
        if value is None:
            raise KeyError(f'Translation key="{self.key}" not found')
        return value


class I18NFormatGetter(Text):
    """
    Рендерит шаблон и подставляет значения по выражениям в фигурных скобках.

    Поддержка внутри {…}:
      - литералы: str, int, float, bool, None, list, tuple, dict;
      - имена из `data`: `name`;
      - атрибуты: `name.attr`;
      - индексация/ключ: `name[0]`, `name["key"]`.

    Вызовы функций, операции, срезы и т.п. — запрещены.
    Если выражение вычисляется в строку — трактуется как i18n-ключ и заменяется переводом.
    """

    def __init__(self, template: str, when: WhenCondition | None = None) -> None:
        """
        Args:
            template: Шаблон, например: "User: {user.name}, id: {user['id']}"
            when: Условие видимости виджета.

        """
        super().__init__(when)
        self.template = template
        self._pattern: re.Pattern[str] = re.compile(r"{([^{}]+)}")

    async def _render_text(self, data: dict[str, Any], dialog_manager: DialogManager) -> str:
        """
        Обрабатывает шаблон, подставляет значения/переводы и возвращает готовую строку.

        Returns:
            Итоговая строка.

        Raises:
            RuntimeError: Нет `i18n` в `middleware_data`.
            KeyError: Ключ перевода не найден.
            ValueError: Некорректное/запрещённое выражение.

        """
        i18n = dialog_manager.middleware_data.get("i18n")
        if not i18n:
            raise RuntimeError("TranslatorRunner 'i18n' not found in middleware_data")

        def replace(match: re.Match[str]) -> str:
            expr = match.group(1).strip()
            try:
                raw_value: Any = self.safe_eval_expr(expr, data)
            except Exception as e:
                raise ValueError(f"Invalid format expression: {{{expr}}}") from e

            if isinstance(raw_value, str):
                translated = i18n.get(raw_value, **data)
                if translated is None:
                    raise KeyError(f'Translation key="{raw_value}" not found')
                return translated
            return str(raw_value)

        return self._pattern.sub(replace, self.template)

    @staticmethod
    def safe_eval_expr(expr: str, data: Mapping[str, Any]) -> Any:
        """
        Безопасно вычисляет строго ограничённое выражение.

        Returns:
            Результат вычисления.

        Raises:
            ValueError: Запрещённая конструкция.
            NameError: Имя отсутствует в `data`.
            KeyError: Ключ/индекс отсутствует.
            AttributeError: Атрибут отсутствует.
            TypeError: Недопустимый тип индексации или использование среза.

        """
        root: ast.Expression = ast.parse(expr, mode="eval")
        return I18NFormatGetter._eval_node(root, data)

    @staticmethod
    def _eval_node(node: ast.AST, data: Mapping[str, Any]) -> Any:
        """
        Диспетчер по типам узлов AST с делегированием в простые хелперы.

        Args:
            node: Текущий узел AST.
            data: Контекст значений, доступных по именам.

        Returns:
            Результат вычисления узла.

        Raises:
            TypeError: Для неподдерживаемых типов узлов.
            NameError: Если имя отсутствует в data.
            KeyError: Если ключ/индекс отсутствует.
            AttributeError: Если атрибут отсутствует.
            TypeError: Если индексирование недопустимо.

        """
        value: Any  # единая точка возврата

        if isinstance(node, ast.Expression):
            value = I18NFormatGetter._eval_node(cast("ast.AST", node.body), data)

        elif isinstance(node, ast.Constant):
            value = node.value

        elif isinstance(node, ast.Name):
            value = I18NFormatGetter._eval_name(node, data)

        elif isinstance(node, ast.Attribute):
            value = I18NFormatGetter._eval_attribute(node, data)

        elif isinstance(node, ast.Subscript):
            value = I18NFormatGetter._eval_subscript(node, data)

        elif isinstance(node, ast.Tuple):
            value = tuple(I18NFormatGetter._eval_node(cast("ast.AST", elt), data) for elt in node.elts)

        elif isinstance(node, ast.List):
            value = [I18NFormatGetter._eval_node(cast("ast.AST", elt), data) for elt in node.elts]

        elif isinstance(node, ast.Dict):
            value = {
                I18NFormatGetter._eval_node(cast("ast.AST", k), data): I18NFormatGetter._eval_node(
                    cast("ast.AST", v), data
                )
                for k, v in zip(node.keys, node.values, strict=False)
                if k is not None and v is not None
            }

        else:
            raise TypeError(f"disallowed expression: {node.__class__.__name__}")

        return value

    @staticmethod
    def _eval_name(node: ast.Name, data: Mapping[str, Any]) -> Any:
        """
        Возвращает значение имени из `data`.

        Raises:
            NameError: Имя отсутствует.

        """
        if node.id in data:
            return data[node.id]
        raise NameError(f"name '{node.id}' is not defined")

    @staticmethod
    def _eval_attribute(node: ast.Attribute, data: Mapping[str, Any]) -> Any:
        """
        Вычисляет доступ к атрибуту: obj.attr.

        Args:
            node: Узел Attribute.
            data: Контекст значений.

        Returns:
            Значение атрибута.

        Raises:
            AttributeError: Если атрибут отсутствует у объекта.

        """
        obj = I18NFormatGetter._eval_node(cast("ast.AST", node.value), data)
        return getattr(obj, node.attr)

    @staticmethod
    def _eval_subscript(node: ast.Subscript, data: Mapping[str, Any]) -> Any:
        """
        Вычисляет индексацию/доступ по ключу: obj[key]. Срезы запрещены.

        Args:
            node: Узел Subscript.
            data: Контекст значений.

        Returns:
            Значение obj[key].

        Raises:
            TypeError: Если используется срез, slice отсутствует, или тип некорректен.
            KeyError: Если ключ отсутствует в контейнере.
            IndexError: Если индекс вне диапазона.

        """
        obj = I18NFormatGetter._eval_node(cast("ast.AST", node.value), data)

        sl = node.slice
        if sl is None:
            raise TypeError("subscript slice is None")

        if isinstance(sl, ast.Slice):
            raise TypeError("slices are not allowed")

        key = I18NFormatGetter._eval_node(cast("ast.AST", sl), data)
        return obj[key]
