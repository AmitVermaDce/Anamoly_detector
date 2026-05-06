from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from app.core.config import get_settings


def get_application_logger() -> Any:
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=settings.log_format,
        colorize=True,
        enqueue=True,
    )
    return logger
