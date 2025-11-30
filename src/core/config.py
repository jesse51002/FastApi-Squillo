"""Application configuration using environment variables."""

import logging
import sys

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Auto-load environment variables from .env file
load_dotenv()


class AppConfig(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API Configuration
    mistral_api_key: str
    claude_api_key: str
    gemini_api_key: str

    # External API Configuration
    ensemble_data_api_key: str

    # API Configuration
    api_title: str = "FastAPI Squillo"
    api_version: str = "0.1.0"
    api_description: str = "FastAPI application with LLM service integration"

    # CORS Configuration
    cors_origins: str = "*"
    cors_credentials: bool = True
    cors_methods: str = "*"
    cors_headers: str = "*"

    # Logging Configuration
    log_level: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Global config instance
settings = AppConfig()  # pyright: ignore (Parameters are instantiated by env)


def setup_logging(log_level: str | None = None) -> None:
    """Setup logging configuration for the application.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If not provided, uses the log_level from settings.
    """
    # Use provided log_level or fall back to settings
    level_str = log_level or settings.log_level
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Warning for library requests

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("src").setLevel(level)


# Initialize logging on import
setup_logging()
