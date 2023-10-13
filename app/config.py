import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="rcp_")

    port: int = 8000
    """
    The port to bind to. Defaults to 8000.  This is set from uvicorn's --port flag.
    its only available here for reference.
    """

    host: str = ""
    """
    The host to bind to. Defaults to ''. This is set from uvicorn's --host flag.
    its only available here for reference.
    """

    auth_key: str = ""
    """
    The authentication key for the API. If set, all requests must include the header
    `Authorization: <auth_key>`.
    """

    commit: str = "nightly"
    """
    The commit hash of the current build. This is set by the build script via docker build args.
    """


@functools.lru_cache
def settings() -> Settings:
    return Settings()
