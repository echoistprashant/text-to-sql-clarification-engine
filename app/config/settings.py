import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


DEFAULT_APP_NAME = "Text-to-SQL Clarification Engine"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_RETRY_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    log_level: str
    database_url: str
    gemini_api_key: str | None
    gemini_model: str
    gemini_max_retries: int
    gemini_initial_retry_delay_seconds: float
    gemini_timeout_seconds: float
    openrouter_api_key: str | None = None
    openrouter_model: str = DEFAULT_OPENROUTER_MODEL
    llm_provider: str = "gemini"
    llm_max_retries: int = DEFAULT_MAX_RETRIES
    llm_initial_retry_delay_seconds: float = DEFAULT_INITIAL_RETRY_DELAY_SECONDS
    llm_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def _get_required(
    name: str,
) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} environment variable is not set.")

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
        raise RuntimeError(f"{name} must be an integer.") from exc

    if parsed < 0:
        raise RuntimeError(f"{name} must be non-negative.")

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
        raise RuntimeError(f"{name} must be a number.") from exc

    if parsed < 0:
        raise RuntimeError(f"{name} must be non-negative.")

    return parsed


def get_settings() -> Settings:
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    provider_env = os.getenv("LLM_PROVIDER")
    if provider_env:
        llm_provider = provider_env.lower()
    elif openrouter_key:
        llm_provider = "openrouter"
    else:
        llm_provider = "gemini"

    # Require at least one valid key for the selected provider
    if llm_provider == "openrouter":
        if not openrouter_key and not gemini_key:
            raise RuntimeError("OPENROUTER_API_KEY environment variable is not set.")
    else:
        if not gemini_key and not openrouter_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    max_retries = _get_int(
        "LLM_MAX_RETRIES",
        _get_int("GEMINI_MAX_RETRIES", DEFAULT_MAX_RETRIES),
    )
    initial_delay = _get_float(
        "LLM_INITIAL_RETRY_DELAY_SECONDS",
        _get_float(
            "GEMINI_INITIAL_RETRY_DELAY_SECONDS", DEFAULT_INITIAL_RETRY_DELAY_SECONDS
        ),
    )
    timeout = _get_float(
        "LLM_TIMEOUT_SECONDS",
        _get_float("GEMINI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
    )

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
        gemini_api_key=gemini_key,
        gemini_model=os.getenv(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL,
        ),
        gemini_max_retries=max_retries,
        gemini_initial_retry_delay_seconds=initial_delay,
        gemini_timeout_seconds=timeout,
        openrouter_api_key=openrouter_key,
        openrouter_model=os.getenv(
            "OPENROUTER_MODEL",
            DEFAULT_OPENROUTER_MODEL,
        ),
        llm_provider=llm_provider,
        llm_max_retries=max_retries,
        llm_initial_retry_delay_seconds=initial_delay,
        llm_timeout_seconds=timeout,
    )
