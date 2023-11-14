import asyncio
import logging
from typing import Any

import httpx
from pydantic import AnyHttpUrl, BaseModel
from recipe_scrapers import scrape_html
from recipe_scrapers._abstract import AbstractScraper

from app.scraper.recipe import Recipe


class CleanedResponse(BaseModel):
    url: str
    data: Recipe
    errors: str | None = None


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
    if scraper.schema.data and isinstance(scraper.schema.data, dict):
        scraper.schema.data["@content"] = "schema"

        maybeIngredients = maybe(scraper.ingredients, [])
        if len(maybeIngredients) > 0:
            scraper.schema.data["ingredients"] = maybeIngredients

        maybeInstructions = maybe(scraper.instructions_list, [])
        if len(maybeInstructions) > 0:
            scraper.schema.data["instructions"] = scraper.instructions()

        return scraper.schema.data

    return {
        "@content": "wild",
        "name": maybe(scraper.title, ""),
        "author": maybe(scraper.author, ""),
        "description": maybe(scraper.description, ""),
        "image": maybe(scraper.image, ""),
        "ingredients": maybe(scraper.ingredients, []),
        "instructions": maybe(scraper.instructions_list, []),
        "totalTime": str(maybe(scraper.total_time, "")),
        "prepTime": str(maybe(scraper.prep_time, "")),
        "cooktime": str(maybe(scraper.cook_time, "")),
        "nutrition": maybe(scraper.nutrients, {}),
        "recipeYield": maybe(scraper.yields, ""),
        "review": maybe(scraper.reviews, []),
        "recipeCategory": maybe(scraper.category, ""),
        "ratings": maybe(scraper.ratings, ""),
        "recipeCuisine": maybe(scraper.cuisine, ""),
        "links": maybe(scraper.links, []),
        "siteName": maybe(scraper.site_name, ""),
    }





class ScrapeJob:
    def __init__(self, url: AnyHttpUrl, html: str | None):
        self.url = url
        self.html = html


class ScrapeResult:
    def __init__(self, url: str, data: Recipe, error: Exception | None):
        self.url = url
        self.data = data
        self.error = error


async def scrape_recipe_v2(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    html: str | None,
) -> ScrapeResult:
    if not html:
        r = await client.get(url, headers=headers)
        logging.info(f"GET {url} {r.status_code}")
        html = r.text
    else:
        logging.debug(f"Using cached HTML for {url}")

    scrape_result = None
    try:
        scrape_result = scrape_html(html, org_url=url)
    except Exception as e:
        return ScrapeResult(url=url, data={}, error=e)

    schema_data = None
    try:
        schema_data = to_schema_data(scrape_result)
    except Exception as e:
        return ScrapeResult(url=url, data={}, error=e)

    return ScrapeResult(url=url, data=schema_data, error=None)


async def scrape_urls_v2(jobs: list[ScrapeJob]) -> list[ScrapeResult]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}

    async with httpx.AsyncClient() as client:
        tasks = [scrape_recipe_v2(client, job.url.unicode_string(), headers, job.html) for job in jobs]
        result = await asyncio.gather(*tasks)

    return result
