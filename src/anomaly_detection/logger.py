import sys
from loguru import logger

from anomaly_detection.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=settings.log_format,
        colorize=True,
        enqueue=True,
    )
