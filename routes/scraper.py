import asyncio
from typing import Any

import httpx
from recipe_scrapers import scrape_html
from recipe_scrapers._abstract import AbstractScraper
from starlette.responses import JSONResponse


def maybe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def to_schema_data(scraper: AbstractScraper) -> dict[str, Any]:
    if scraper.schema.data:
        return scraper.schema.data

    return {
        "@content": "wild",
        "name": maybe(scraper.title, ""),
        "author": maybe(scraper.author, ""),
        "description": maybe(scraper.description, ""),
        "image": maybe(scraper.image, ""),
        "ingredients": maybe(scraper.ingredients, []),
        "instructions": maybe(scraper.instructions_list, []),
        "totalTime": maybe(scraper.total_time, ""),
        "prepTime": maybe(scraper.prep_time, ""),
        "cooktime": maybe(scraper.cook_time, ""),
        "nutrition": maybe(scraper.nutrients, {}),
        "recipeYield": maybe(scraper.yields, ""),
        "review": maybe(scraper.reviews, []),
        "recipeCategory": maybe(scraper.category, ""),
        "ratings": maybe(scraper.ratings, ""),
        "recipeCuisine": maybe(scraper.cuisine, ""),
        "links": maybe(scraper.links, []),
        "siteName": maybe(scraper.site_name, ""),
    }


async def scarpe_recipe(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
) -> dict:
    r = await client.get(url, headers=headers)
    return {
        "url": url,
        "data": to_schema_data(scrape_html(r.text, org_url=url)),
    }


async def scrape_urls(urls: list[str]) -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"
    }

    async with httpx.AsyncClient() as client:
        tasks = [scarpe_recipe(client, url, headers) for url in urls]
        result = await asyncio.gather(*tasks)

    return result


async def scrape(request):
    body = await request.json()

    url: list[str] = body.get("urls")

    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)

    if len(url) > 10:
        return JSONResponse(
            {"error": "too many urls, max 10 per request"}, status_code=400
        )

    return JSONResponse(await scrape_urls(url))
