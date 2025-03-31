import logging
from colorlog import ColoredFormatter

logger = logging.getLogger("litecache")
handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter(
        "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "ERROR": "red",
        },
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

from .server import LiteCache
from .parser import RespParser


__all__ = ["LiteCache", "RespParser", "logger"]
