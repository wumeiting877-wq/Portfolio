import os

from app.scripts.bootstrap import demo_accounts_enabled


def test_development_keeps_demo_accounts(monkeypatch) -> None:
    monkeypatch.delenv("BOOTSTRAP_DEMO_ACCOUNTS", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    assert demo_accounts_enabled() is True


def test_test_env_keeps_demo_accounts(monkeypatch) -> None:
    monkeypatch.delenv("BOOTSTRAP_DEMO_ACCOUNTS", raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    assert demo_accounts_enabled() is True


def test_unset_env_follows_settings_development(monkeypatch) -> None:
    monkeypatch.delenv("BOOTSTRAP_DEMO_ACCOUNTS", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    assert demo_accounts_enabled() is True


def test_production_skips_demo_accounts(monkeypatch) -> None:
    monkeypatch.delenv("BOOTSTRAP_DEMO_ACCOUNTS", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    assert demo_accounts_enabled() is False


def test_pilot_env_name_skips_demo_accounts(monkeypatch) -> None:
    monkeypatch.delenv("BOOTSTRAP_DEMO_ACCOUNTS", raising=False)
    monkeypatch.setenv("APP_ENV", "pilot")
    assert demo_accounts_enabled() is False


def test_explicit_true_overrides_production(monkeypatch) -> None:
    monkeypatch.setenv("BOOTSTRAP_DEMO_ACCOUNTS", "true")
    monkeypatch.setenv("APP_ENV", "production")
    assert demo_accounts_enabled() is True


def test_explicit_false_overrides_development(monkeypatch) -> None:
    monkeypatch.setenv("BOOTSTRAP_DEMO_ACCOUNTS", "false")
    monkeypatch.setenv("APP_ENV", "development")
    assert demo_accounts_enabled() is False


def test_blank_flag_is_treated_as_unset(monkeypatch) -> None:
    monkeypatch.setenv("BOOTSTRAP_DEMO_ACCOUNTS", "  ")
    monkeypatch.setenv("APP_ENV", "production")
    assert demo_accounts_enabled() is False
    monkeypatch.setenv("APP_ENV", "development")
    assert demo_accounts_enabled() is True
