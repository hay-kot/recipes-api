from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import Annotated

from pkg.schema.scrapers import CleanedScrapeResponse, ScrapeError, ScrapeRequest, ScrapeResponse
from pkg.schema.web import Context
from pkg.services.cleaner import cleaner
from pkg.services.parser.nlp_parser import dict_to_parsed_nutrition, list_to_parsed_ingredients
from pkg.services.recipes.recipe import Recipe
from pkg.services.recipes.scraper import scrape_urls

router = APIRouter(tags=["Recipe Web Scrapers"])


@router.post("/recipes/scrape", response_model=list[ScrapeResponse] | list[CleanedScrapeResponse])
async def scrape_recipe(ctx: Annotated[Context, Depends(Context)], req: list[ScrapeRequest], clean: bool = True):
    """
    Scrape a list of URLs and return the raw recipe data.
    """
    if len(req) == 0:
        raise HTTPException(status_code=400, detail={"error": "no urls or html provided"})

    data = await scrape_urls(ctx, req)

    results = []
    for d in data:
        if d.error:
            results.append(ScrapeResponse(url=d.url, data=None, error=ScrapeError.from_exception(d.error)))
            continue

        if not clean:
            results.append(ScrapeResponse(url=d.url, data=d.data, error=None))
            continue

        cleaned = Recipe(**cleaner.clean(d.data, d.url))

        parsed_ingredients = list_to_parsed_ingredients(cleaned.ingredients, ctx)

        parsed_nutrition = []
        if cleaned.nutrition:
            parsed_nutrition = dict_to_parsed_nutrition(cleaned.nutrition)

        results.append(
            CleanedScrapeResponse(
                url=d.url,
                data=cleaned,
                ingredients=parsed_ingredients,
                error=None,
                nutrition=parsed_nutrition,
            )
        )

    return results
