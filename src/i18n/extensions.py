from typing import Any, Optional

from jinja2 import Environment
from jinja2.ext import Extension
from jinja2.nodes import Call, Const, Name, Node, TemplateData, Output

from src.i18n import get_translations, get_locale


class I18nExtension(Extension):
    tags = {"trans"}

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.globals["_"] = _translate
        environment.globals["_i18n_trans"] = _trans_block
        environment.globals["get_available_locales"] = lambda: (
            get_translations().available_locales
        )

    def parse(self, parser: Any) -> Optional[Node]:
        token = next(parser.stream)
        lineno = token.lineno

        count_expr = None
        if parser.stream.current.test("name:count"):
            next(parser.stream)
            parser.stream.expect("assign")
            count_expr = parser.parse_expression()

        body = parser.parse_statements(
            ("name:plural", "name:endtrans"), drop_needle=False
        )

        plural_body = None
        if parser.stream.current.test("name:plural"):
            next(parser.stream)
            plural_body = parser.parse_statements(("name:endtrans",), drop_needle=True)
        else:
            next(parser.stream)

        singular_text = self._extract_text(body)
        plural_text = self._extract_text(plural_body) if plural_body else None

        args: list[Node] = [Const(singular_text), Const(plural_text)]
        if count_expr is not None:
            args.append(count_expr)

        node = Call(Name("_i18n_trans", "load"), args, [], None, None)
        node.set_lineno(lineno)
        return Output([node], lineno=lineno)

    def _extract_text(self, body: list[Any]) -> str:
        parts = []
        for node in body:
            if isinstance(node, TemplateData):
                parts.append(node.data)
            elif isinstance(node, Output):
                for child in node.nodes:
                    if isinstance(child, TemplateData):
                        parts.append(child.data)
                    elif isinstance(child, Name):
                        parts.append("{" + child.name + "}")
                    else:
                        parts.append(str(child))
            else:
                parts.append(str(node))
        return "".join(parts).strip()


def _translate(key: str, **kwargs: Any) -> str:
    store = get_translations()
    locale = get_locale()
    value = store.get(locale, key, default=key)

    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return value


def _trans_block(
    singular: str, plural: Optional[str] = None, count: Any = None, **kwargs: Any
) -> str:
    store = get_translations()
    locale = get_locale()

    if count is not None and plural is not None and int(count) != 1:
        template_text = plural
    else:
        template_text = singular

    translations = store._translations.get(locale, {})
    if locale != "en":
        en_translations = store._translations.get("en", {})
        translated = translations.get(singular)
        if translated is None:
            translated = en_translations.get(singular, template_text)
    else:
        translated = translations.get(singular, template_text)

    try:
        return translated.format(count=count, **kwargs)
    except (KeyError, IndexError, AttributeError):
        return translated
