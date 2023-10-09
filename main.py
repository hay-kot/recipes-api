from fastapi import FastAPI
from pydantic import BaseModel

from app import config, logger
from app.ingredient_parser import routes as ingredient_parser_routes
from app.scraper import routes as scraper_routes

settings = config.settings()

app = FastAPI(
    title="Recipe API",
    description="A simple API for parsing recipes and ingredients.",
    version="0.4.2",
)

app.include_router(ingredient_parser_routes.router, prefix="/api")
app.include_router(scraper_routes.router, prefix="/api")


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
