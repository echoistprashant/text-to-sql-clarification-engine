import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


DEFAULT_APP_NAME = (
    "Text-to-SQL Clarification Engine"
)
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_RETRY_DELAY_SECONDS = 1.0
DEFAULT_GEMINI_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    log_level: str
    database_url: str
    gemini_api_key: str
    gemini_model: str
    gemini_max_retries: int
    gemini_initial_retry_delay_seconds: float
    gemini_timeout_seconds: float


def _get_required(
    name: str,
) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} environment variable is not set."
        )

    return value


def _get_int(
    name: str,
    default: int,
) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer."
        ) from exc

    if parsed < 0:
        raise RuntimeError(
            f"{name} must be non-negative."
        )

    return parsed


def _get_float(
    name: str,
    default: float,
) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed = float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be a number."
        ) from exc

    if parsed < 0:
        raise RuntimeError(
            f"{name} must be non-negative."
        )

    return parsed


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv(
            "APP_NAME",
            DEFAULT_APP_NAME,
        ),
        app_version=os.getenv(
            "APP_VERSION",
            DEFAULT_APP_VERSION,
        ),
        environment=os.getenv(
            "APP_ENVIRONMENT",
            DEFAULT_ENVIRONMENT,
        ),
        log_level=os.getenv(
            "LOG_LEVEL",
            DEFAULT_LOG_LEVEL,
        ).upper(),
        database_url=_get_required(
            "DATABASE_URL",
        ),
        gemini_api_key=_get_required(
            "GEMINI_API_KEY",
        ),
        gemini_model=os.getenv(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL,
        ),
        gemini_max_retries=_get_int(
            "GEMINI_MAX_RETRIES",
            DEFAULT_MAX_RETRIES,
        ),
        gemini_initial_retry_delay_seconds=_get_float(
            "GEMINI_INITIAL_RETRY_DELAY_SECONDS",
            DEFAULT_INITIAL_RETRY_DELAY_SECONDS,
        ),
        gemini_timeout_seconds=_get_float(
            "GEMINI_TIMEOUT_SECONDS",
            DEFAULT_GEMINI_TIMEOUT_SECONDS,
        ),
    )