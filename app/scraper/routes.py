from fastapi import APIRouter, HTTPException
from pydantic import AnyHttpUrl, BaseModel

from app.scraper.cleaner.cleaner import clean
from app.scraper.scraper import CleanedResponse, ScrapeResponse, scrape_urls

router = APIRouter(tags=["Recipe Web Scraper"])


class ScrapeRequest(BaseModel):
    urls: list[AnyHttpUrl]
    html: dict[AnyHttpUrl, str] = {}


@router.post("/v1/scrape", response_model=list[ScrapeResponse])
async def scrape_recipe(req: ScrapeRequest):
    """
    Scrape a list of URLs and return the raw recipe data.
    """
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(
            status_code=400, detail={"error": "No URLs or HTML provided."}
        )

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    return await scrape_urls(req.urls, req.html)


@router.post("/v1/scrape/clean", response_model=list[CleanedResponse])
async def scrape_recipe_clean(req: ScrapeRequest):
    """
    Scrape a list of URLs and return the cleaned recipe data.
    """
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
