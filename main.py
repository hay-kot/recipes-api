import logging

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from pydantic import AnyHttpUrl, BaseModel

from routes import crfpp
from routes.cleaner import clean
from routes.parser import ParseResponse
from routes.scraper import CleanedResponse, ScrapeResponse, scrape_urls

logging.basicConfig(
    # standard logging config
    format="[%(levelname)s] %(asctime)s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


app = FastAPI(
    title="Recipe API",
    description="A simple API for parsing recipes and ingredients.",
    version="0.4.2",
)


@app.get("/ready")
def ready():
    return {"status": "ok"}


class ScrapeRequest(BaseModel):
    urls: list[AnyHttpUrl]
    html: dict[AnyHttpUrl, str] = {}


@app.post("/api/v1/scrape", response_model=list[ScrapeResponse])
async def scrape_recipe(req: ScrapeRequest):
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(
            status_code=400, detail={"error": "No URLs or HTML provided."}
        )

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    return await scrape_urls(req.urls, req.html)


@app.post("/api/v1/scrape/clean", response_model=list[CleanedResponse])
async def scrape_recipe_clean(req: ScrapeRequest):
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(
            status_code=400, detail={"error": "No URLs or HTML provided."}
        )

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    data = await scrape_urls(req.urls, req.html)

    for d in data:
        d.data = clean(d.data, d.url)

    return data


class ParseRequest(BaseModel):
    ingredients: list[str]


@app.post("/api/v1/parse", response_model=list[ParseResponse])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)
