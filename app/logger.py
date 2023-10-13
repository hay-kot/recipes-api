import functools
import logging as stdlog

__all__ = ["logger"]


@functools.lru_cache
def logger() -> stdlog.Logger:
    stdlog.basicConfig(
        # standard logging config
        format="[%(levelname)s] %(asctime)s %(message)s",
        level=stdlog.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return stdlog.getLogger("app")
