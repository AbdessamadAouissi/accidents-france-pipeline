"""Logger structuré via loguru."""

import sys

from loguru import logger as _logger

from src.utils.config import settings

_logger.remove()
_logger.add(
    sys.stderr,
    level=settings.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    colorize=True,
)


def get_logger(name: str | None = None):
    return _logger.bind(scope=name) if name else _logger
