from fastapi import APIRouter, HTTPException

from app.ingredient_parser import crfpp
from app.scraper.cleaner.cleaner import clean
from app.scraper.recipe import Recipe
from app.scraper.scraper import scrape_urls_v2

from .schemas import CleanedScrapeResponse, ParsedIngredients, ParseRequest, ScrapeError, ScrapeRequest, ScrapeResponse

router = APIRouter()


@router.post("/scrape", response_model=list[ScrapeResponse], tags=["Recipe Web Scraper"])
async def scrape_recipe(req: list[ScrapeRequest]):
    """
    Scrape a list of URLs and return the raw recipe data.
    """
    if len(req) == 0:
        raise HTTPException(status_code=400, detail={"error": "no urls or html provided"})

    data = await scrape_urls_v2(req)

    results = []
    for d in data:
        if d.error:
            results.append(ScrapeResponse(url=d.url, data=None, error=ScrapeError.from_exception(d.error)))
            continue

        results.append(ScrapeResponse(url=d.url, data=d.data, error=None))

    return results


@router.post("/scrape/clean", response_model=list[CleanedScrapeResponse], tags=["Recipe Web Scraper"])
async def scrape_recipe_clean(req: list[ScrapeRequest]):
    """
    Scrape a list of URLs and return the cleaned recipe data.
    """
    if len(req) == 0:
        raise HTTPException(status_code=400, detail={"error": "no urls or html provided"})

    data = await scrape_urls_v2(req)

    results = []
    for d in data:
        if d.error:
            results.append(
                CleanedScrapeResponse(
                    url=d.url,
                    data=None,
                    ingredients=None,
                    error=ScrapeError.from_exception(d.error),
                )
            )
            continue

        cleaned = Recipe(**clean(d.data, d.url))

        parsed_ingredients = []
        for i in crfpp.convert_list_to_crf_model(cleaned.ingredients):
            parsed_ingredients.append(
                ParsedIngredients(
                    input=i.input,
                    name=i.name,
                    qty=i.qty if i.qty else 0.0,
                    unit=i.unit,
                    comment=i.comment,
                    other=i.other,
                )
            )

        results.append(
            CleanedScrapeResponse(
                url=d.url,
                data=cleaned,
                ingredients=parsed_ingredients,
                error=None,
            )
        )

    return results


@router.post("/parse", response_model=list[ParsedIngredients], tags=["Ingredient Parser"])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)
