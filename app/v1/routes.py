from fastapi import APIRouter, HTTPException

from app.ingredient_parser import crfpp
from app.scraper.cleaner.cleaner import clean
from app.scraper.scraper import CleanedResponse, ScrapeResponse, scrape_urls

from .schemas import ParseRequest, ParseResponse, ScrapeRequest

router = APIRouter()

@router.post("/scrape", response_model=list[ScrapeResponse], tags=["Recipe Web Scraper"])
async def scrape_recipe(req: ScrapeRequest):
    """
    Scrape a list of URLs and return the raw recipe data.
    """
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(status_code=400, detail={"error": "No URLs or HTML provided."})

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    return await scrape_urls(req.urls, req.html)


@router.post("/scrape/clean", response_model=list[CleanedResponse], tags=["Recipe Web Scraper"])
async def scrape_recipe_clean(req: ScrapeRequest):
    """
    Scrape a list of URLs and return the cleaned recipe data.
    """
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(status_code=400, detail={"error": "No URLs or HTML provided."})

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    data = await scrape_urls(req.urls, req.html)

    for d in data:
        d.data = clean(d.data, d.url)

    return data


@router.post("/parse", response_model=list[ParseResponse], tags=["Ingredient Parser"])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)
