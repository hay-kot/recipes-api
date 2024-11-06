from logging import Logger
from typing import Annotated

from fastapi import Header

from pkg.core.logger import logger


class Context:
    request_id: str
    logger: Logger

    def __init__(self, x_request_id: Annotated[str | None, Header()] = "") -> None:
        self.request_id = x_request_id
        self.logger = logger()

    def kv(self) -> str:
        return f"rid={self.request_id}"
