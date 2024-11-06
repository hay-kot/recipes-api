from fastapi import APIRouter

from .. import core
from ..schema import system as schema

router = APIRouter(prefix="/system", tags=["System"])
settings = core.settings()


@router.get("/ready")
def ready() -> schema.Health:
    return schema.Health(status="ok")


@router.get("/info")
def info() -> schema.AppInfo:
    return schema.AppInfo(version="", commit=settings.commit)
