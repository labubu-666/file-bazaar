import json
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

from starlette.requests import Request

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "en"

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)


def set_locale(locale: str) -> None:
    _current_locale.set(locale)


def get_locale() -> str:
    return _current_locale.get()


class TranslationStore:
    def __init__(self) -> None:
        self._translations: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not LOCALES_DIR.is_dir():
            logger.warning("Locales directory not found: %s", LOCALES_DIR)
            return

        for path in LOCALES_DIR.glob("*.json"):
            locale = path.stem
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._translations[locale] = data
                logger.info("Loaded translations for locale: %s", locale)
            except Exception:
                logger.exception("Failed to load translations for %s", locale)

    def get(
        self, locale: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        translations = self._translations.get(locale, {})
        value = translations.get(key)
        if value is not None:
            return str(value)
        if locale != DEFAULT_LOCALE:
            return self._translations.get(DEFAULT_LOCALE, {}).get(key, default)
        return default or key

    @property
    def available_locales(self) -> list[str]:
        return sorted(self._translations.keys())


_store: Optional[TranslationStore] = None


def init_translations() -> TranslationStore:
    global _store
    _store = TranslationStore()
    return _store


def get_translations() -> TranslationStore:
    if _store is None:
        return init_translations()
    return _store


def resolve_locale(request: Request, default: Optional[str] = None) -> str:
    from src.core.settings import settings

    if default is None:
        default = settings.default_locale

    lang = request.query_params.get("lang")
    if lang and lang in get_translations().available_locales:
        return lang

    locale_cookie = request.cookies.get("locale")
    if locale_cookie and locale_cookie in get_translations().available_locales:
        return locale_cookie

    accept_language = request.headers.get("accept-language", "")
    if accept_language:
        for part in accept_language.split(","):
            code = part.strip().split(";")[0].strip()[:2]
            if code in get_translations().available_locales:
                return code

    return default
