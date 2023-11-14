from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import __version__, config, logger, v2

settings = config.settings()

app = FastAPI(
    title="Recipe API",
    description="A simple API for parsing recipes and ingredients.",
    version=__version__,
)


app.add_middleware(GZipMiddleware, minimum_size=1000)


def mount_auth_middleware(app: FastAPI) -> None:
    async def auth_middleware(request: Request, call_next):
        if request.url.path.startswith("/api"):
            auth_header = request.headers.get("Authorization")

            if auth_header is None or auth_header != settings.auth_key:
                return JSONResponse(status_code=401, content={"message": "Unauthorized"})
        return await call_next(request)

    app.middleware("http")(auth_middleware)


if settings.auth_key:
    mount_auth_middleware(app)


app.include_router(v2.router, prefix="/api/v2")


@app.on_event("startup")
def startup() -> None:
    log = logger.logger()
    log.info("server started")
    log.info("swagger docs available at http://localhost:%d/docs", settings.port)


class Health(BaseModel):
    status: str


@app.get("/ready", tags=["Health"])
def ready() -> Health:
    return Health(status="ok")


class AppInfo(BaseModel):
    version: str
    commit: str


@app.get("/info", tags=["Health"])
def info() -> AppInfo:
    return AppInfo(version=__version__, commit=settings.commit)
