import functools
import logging as stdlog

from .config import settings

__all__ = ["logger"]


@functools.lru_cache
def logger() -> stdlog.Logger:
    stdlog.basicConfig(
        # standard logging config
        format="[%(levelname)s] %(asctime)s %(message)s",
        level=settings().log_level.upper(),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return stdlog.getLogger("app")
