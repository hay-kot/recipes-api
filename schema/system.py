from pydantic import BaseModel


class Health(BaseModel):
    status: str


class AppInfo(BaseModel):
    version: str
    commit: str
