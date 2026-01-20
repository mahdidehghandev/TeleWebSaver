import logging

from decouple import config as _config


logger = logging.getLogger("telewebsaver.config")


def get_bot_token() -> str:
    token = _config("TELEGRAM_BOT_TOKEN", default=None)
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set (check your environment or .env file)")
    return token


def get_searxng_base_url() -> str:
    return _config("SEARXNG_URL", default="http://localhost:8080").rstrip("/")

