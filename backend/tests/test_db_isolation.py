from app.core.config import settings
from app.core.database import engine
from tests.conftest import TEST_DB_NAME


def test_pytest_uses_isolated_test_database() -> None:
    assert settings.POSTGRES_DB == TEST_DB_NAME
    assert "test" in settings.POSTGRES_DB.lower()
    assert settings.POSTGRES_DB != "project_cost_hub"
    assert engine.url.database == TEST_DB_NAME
    assert engine.url.database != "project_cost_hub"


def test_pytest_refuses_development_database_name() -> None:
    assert settings.POSTGRES_TEST_DB == "project_cost_hub_test"
    assert settings.POSTGRES_DB.endswith("_test")
