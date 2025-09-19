import functools

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="recipes_")

    port: int = 8080
    """
    The port to bind to. Defaults to 8080.
    """

    host: str = "0.0.0.0"
    """
    The host to bind to. Defaults to ''.
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

    dev: bool = False
    """
    dev enables development workflows like live reloading.
    """

    log_level: str = "INFO"
    """
    python logging levels
    """

    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"

    otel_endpoint: str = ""
    """
    OpenTelemetry OTLP endpoint for exporting traces. If empty, telemetry will be disabled.
    """


@functools.lru_cache
def settings() -> Settings:
    return Settings()
