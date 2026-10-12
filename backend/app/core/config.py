from functools import lru_cache
import base64
import binascii
import re
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_SECRETS = {"change_me", "changeme", "secret", "jwt-secret", "password"}
_CREDENTIAL_KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "project-cost-hub"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    BACKEND_PORT: int = 8010
    FRONTEND_PORT: int = 5173

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "project_cost_hub"
    POSTGRES_TEST_DB: str = "project_cost_hub_test"
    POSTGRES_USER: str = "project_cost"
    POSTGRES_PASSWORD: str = "change_me"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "change_me"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    RESOURCE_CREDENTIALS_ENABLED: bool = False
    CREDENTIAL_MASTER_KEY: str = ""
    CREDENTIAL_ACTIVE_KEY_ID: str = ""

    @property
    def database_url(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.strip().lower() == "production"


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    lowered = value.strip().lower()
    return lowered in PLACEHOLDER_SECRETS or "change_me" in lowered


def validate_runtime_config(values: Settings | None = None) -> None:
    current = values or get_settings()
    origins = current.cors_origin_list
    if "*" in origins:
        raise RuntimeError("CORS 不允许无条件 *")
    if current.RESOURCE_CREDENTIALS_ENABLED:
        if not current.CREDENTIAL_MASTER_KEY:
            raise RuntimeError("Resource credential master key is required")
        try:
            key = base64.b64decode(current.CREDENTIAL_MASTER_KEY, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("Resource credential master key is invalid") from exc
        if len(key) != 32:
            raise RuntimeError("Resource credential master key must decode to 32 bytes")
        if not _CREDENTIAL_KEY_ID_PATTERN.fullmatch(current.CREDENTIAL_ACTIVE_KEY_ID):
            raise RuntimeError("Resource credential active key ID is invalid")
    if not current.is_production:
        return
    if current.DEBUG:
        raise RuntimeError("production 必须关闭 debug")
    if _is_placeholder(current.JWT_SECRET_KEY):
        raise RuntimeError("production 禁止使用示例 JWT_SECRET_KEY")
    if _is_placeholder(current.POSTGRES_PASSWORD):
        raise RuntimeError("production 禁止使用示例 POSTGRES_PASSWORD")
    if _is_placeholder(current.INITIAL_ADMIN_PASSWORD):
        raise RuntimeError("production 禁止使用示例 INITIAL_ADMIN_PASSWORD")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
