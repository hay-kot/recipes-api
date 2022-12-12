import logging

from fastapi import FastAPI
from pydantic import AnyHttpUrl, BaseModel

from routes import crfpp
from routes.parser import ParseResponse
from routes.scraper import ScrapeResponse, scrape_urls

logging.basicConfig(
    # standard logging config
    format="[%(levelname)s] %(asctime)s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


app = FastAPI(
    title="Recipe API",
    description="A simple API for parsing recipes and ingredients.",
    version="0.2.0",
)


@app.get("/ready")
def ready():
    return {"status": "ok"}


class ScrapeRequest(BaseModel):
    urls: list[AnyHttpUrl]
    html: dict[AnyHttpUrl, str] = {}


@app.post("/api/v1/scrape", response_model=list[ScrapeResponse])
async def scrape_recipe(req: ScrapeRequest):
    return await scrape_urls(req.urls, req.html)


class ParseRequest(BaseModel):
    ingredients: list[str]


@app.post("/api/v1/parse", response_model=list[ParseResponse])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)
