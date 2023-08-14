import asyncio
import logging
from typing import Any

import httpx
from pydantic import AnyHttpUrl, BaseModel
from recipe_scrapers import scrape_html
from recipe_scrapers._abstract import AbstractScraper

from routes.recipe import Recipe


class CleanedResponse(BaseModel):
    url: str
    data: Recipe


class ScrapeResponse(BaseModel):
    url: str
    data: dict[str, Any]


def maybe(fn, default=None):
    try:
        return fn()
    except Exception:
        logging.debug(f"Failed to get {fn.__name__}")
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
    html: str | None,
) -> dict:
    if not html:
        r = await client.get(url, headers=headers)
        logging.info(f"GET {url} {r.status_code}")
        html = r.text
    else:
        logging.debug(f"Using cached HTML for {url}")

    return ScrapeResponse(
        url=url,
        data=to_schema_data(scrape_html(html, org_url=url)),
    )


async def scrape_urls(
    urls: list[AnyHttpUrl], html: dict[str, str] | None
) -> list[ScrapeResponse]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"
    }

    html = html or {}

    async with httpx.AsyncClient() as client:
        tasks = [
            scarpe_recipe(
                client,
                url.unicode_string(),
                headers,
                html.get(url, None),
            )
            for url in urls
        ]
        result = await asyncio.gather(*tasks)

    return result
