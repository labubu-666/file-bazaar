import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from jinja2 import Environment

from src.i18n import (
    TranslationStore,
    get_locale,
    init_translations,
    resolve_locale,
    set_locale,
)
from src.i18n.extensions import I18nExtension


@pytest.fixture(autouse=True)
def _reset_locale():
    set_locale("en")
    yield
    set_locale("en")


@pytest.fixture()
def translations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    en = {"home": "Home", "upload": "Upload", "greeting": "Hello {name}"}
    ja = {"home": "ホーム", "upload": "アップロード"}
    (tmp_path / "en.json").write_text(json.dumps(en), encoding="utf-8")
    (tmp_path / "ja.json").write_text(json.dumps(ja), encoding="utf-8")
    monkeypatch.setattr("src.i18n.LOCALES_DIR", tmp_path)
    store = init_translations()
    return store


@pytest.fixture()
def i18n_env(translations):
    env = Environment(extensions=[I18nExtension])
    return env


def _make_request(
    query: str = "",
    cookies: dict[str, str] | None = None,
    accept_language: str = "",
) -> MagicMock:
    request = MagicMock()
    request.query_params = (
        dict(x.split("=", 1) for x in query.split("&") if x) if query else {}
    )
    request.cookies = cookies or {}
    request.headers = {}
    if accept_language:
        request.headers["accept-language"] = accept_language
    return request


class TestTranslationStore:
    def test_loads_locales(self, translations: TranslationStore):
        assert set(translations.available_locales) == {"en", "ja"}

    def test_get_existing_key(self, translations: TranslationStore):
        assert translations.get("en", "home") == "Home"
        assert translations.get("ja", "home") == "ホーム"

    def test_fallback_to_default_locale(self, translations: TranslationStore):
        assert translations.get("ja", "greeting") == "Hello {name}"

    def test_missing_key_returns_key(self, translations: TranslationStore):
        assert translations.get("en", "nonexistent") == "nonexistent"

    def test_missing_key_with_default(self, translations: TranslationStore):
        assert translations.get("en", "nonexistent", "fallback") == "fallback"


class TestResolveLocale:
    def test_query_param(self, translations):
        request = _make_request(query="lang=ja")
        assert resolve_locale(request) == "ja"

    def test_invalid_query_param_falls_back(self, translations):
        request = _make_request(query="lang=fr")
        assert resolve_locale(request) == "en"

    def test_cookie(self, translations):
        request = _make_request(cookies={"locale": "ja"})
        assert resolve_locale(request) == "ja"

    def test_query_param_overrides_cookie(self, translations):
        request = _make_request(query="lang=ja", cookies={"locale": "en"})
        assert resolve_locale(request) == "ja"

    def test_accept_language(self, translations):
        request = _make_request(accept_language="ja-JP,en;q=0.9")
        assert resolve_locale(request) == "ja"

    def test_default_when_no_match(self, translations):
        request = _make_request()
        assert resolve_locale(request) == "en"


class TestContextVar:
    def test_set_and_get_locale(self):
        set_locale("ja")
        assert get_locale() == "ja"

    def test_default_locale(self):
        set_locale("en")
        assert get_locale() == "en"


class TestI18nExtension:
    def test_translate_function_en(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string("{{ _('home') }}")
        assert tpl.render() == "Home"

    def test_translate_function_ja(self, i18n_env, translations):
        set_locale("ja")
        tpl = i18n_env.from_string("{{ _('home') }}")
        assert tpl.render() == "ホーム"

    def test_translate_with_kwargs(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string("{{ _('greeting', name='World') }}")
        assert tpl.render() == "Hello World"

    def test_translate_missing_key_returns_key(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string("{{ _('missing_key') }}")
        assert tpl.render() == "missing_key"

    def test_trans_tag_singular(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string(
            "{% trans count=1 %}one file{% plural %}many files{% endtrans %}"
        )
        assert tpl.render() == "one file"

    def test_trans_tag_plural(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string(
            "{% trans count=5 %}one file{% plural %}many files{% endtrans %}"
        )
        assert tpl.render() == "many files"

    def test_trans_tag_with_count_variable(self, i18n_env, translations):
        set_locale("en")
        tpl = i18n_env.from_string(
            "{% trans count=n %}{{ count }} file{% plural %}{{ count }} files{% endtrans %}"
        )
        assert tpl.render(n=1) == "1 file"
        assert tpl.render(n=3) == "3 files"

    def test_get_available_locales(self, i18n_env, translations):
        tpl = i18n_env.from_string("{{ get_available_locales() | join(', ') }}")
        assert tpl.render() == "en, ja"


class TestIntegration:
    def test_ui_renders_english(self):
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/ui")
        assert response.status_code == 200
        assert "Home" in response.text

    def test_ui_renders_japanese_via_query(self):
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/ui?lang=ja")
        assert response.status_code == 200
        assert "ホーム" in response.text

    def test_ui_renders_japanese_via_cookie(self):
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app, cookies={"locale": "ja"})
        response = client.get("/ui")
        assert response.status_code == 200
        assert "ホーム" in response.text
