import sys
from loguru import logger
from functools import lru_cache

from src.common.infrastructure.core import settings


@lru_cache
def configure_logger(name: str = "error.log"):
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:DD-MM-YYYY HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )
    logger.add(
        f"logs/{name}",
        rotation="10 MB",
        compression="zip",
        level="ERROR",
        retention="10 day",
        backtrace=True,
        enqueue=True,
        diagnose=True,
    )
    if not settings.DEBUG:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            level="INFO",
            enqueue=True,  # Hace que el logging sea asíncrono (seguro para hilos/multiprocessing)
            backtrace=True,  # Muestra el valor de las variables en el error
            diagnose=True,  # Da detalles extra de dónde falló el código
        )
    return logger
