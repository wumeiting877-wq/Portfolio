import os

from app.scripts.release_smoke_test import resolve_base_url


def test_base_url_env(monkeypatch) -> None:
    monkeypatch.setenv("BASE_URL", "http://127.0.0.1:8011/")
    monkeypatch.delenv("SMOKE_BASE", raising=False)
    assert resolve_base_url([]) == "http://127.0.0.1:8011"


def test_cli_overrides_base_url_env(monkeypatch) -> None:
    monkeypatch.setenv("BASE_URL", "http://127.0.0.1:8011")
    assert resolve_base_url(["--base-url", "http://127.0.0.1:9011"]) == "http://127.0.0.1:9011"


def test_smoke_base_used_when_base_url_missing(monkeypatch) -> None:
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.setenv("SMOKE_BASE", "http://127.0.0.1:8010")
    assert resolve_base_url([]) == "http://127.0.0.1:8010"


def test_default_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("SMOKE_BASE", raising=False)
    assert resolve_base_url([]) == "http://127.0.0.1:8010"
    assert "BASE_URL" not in os.environ
