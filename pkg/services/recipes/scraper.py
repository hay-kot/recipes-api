import asyncio
import logging
from typing import Any

import httpx
import recipe_scrapers._abstract as _rs_abstract
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl, BaseModel
from recipe_scrapers import scrape_html
from recipe_scrapers._abstract import AbstractScraper

from pkg.core.config import settings
from pkg.schema.web import Context

from .recipe import Recipe


def _use_lxml_parser() -> None:
    """Make recipe_scrapers parse the page with lxml instead of its hardcoded
    pure-Python BeautifulSoup("html.parser").

    AbstractScraper.__init__ does ``BeautifulSoup(page_data, "html.parser")``,
    the C-free parser that dominates scrape CPU and allocation churn (the top
    allocator in the memray profile). We wrap the class it references so the
    requested parser is ignored in favour of lxml.
    """

    def _lxml_soup(markup="", *args, **kwargs):
        return BeautifulSoup(markup, "lxml")

    _rs_abstract.BeautifulSoup = _lxml_soup


_use_lxml_parser()

__scrape_headers = {
    "User-Agent": settings().user_agent,
}


class CleanedResponse(BaseModel):
    url: str
    data: Recipe
    errors: str | None = None


class ScrapeResponse(BaseModel):
    url: str
    data: dict[str, Any]


def try_get(fn, default=None):
    try:
        return fn()
    except Exception:
        logging.debug(f"failed to get recipe property {fn.__name__}")
        return default


def to_schema_data(scraper: AbstractScraper) -> dict[str, Any]:
    if scraper.schema.data and isinstance(scraper.schema.data, dict):
        scraper.schema.data["@content"] = "schema"

        maybeIngredients = try_get(scraper.ingredients, [])
        if len(maybeIngredients) > 0:
            scraper.schema.data["ingredients"] = maybeIngredients

        maybeInstructions = try_get(scraper.instructions_list, [])
        if len(maybeInstructions) > 0:
            scraper.schema.data["instructions"] = scraper.instructions()

        return scraper.schema.data

    return {
        "@content": "wild",
        "name": try_get(scraper.title, ""),
        "author": try_get(scraper.author, ""),
        "description": try_get(scraper.description, ""),
        "image": try_get(scraper.image, ""),
        "ingredients": try_get(scraper.ingredients, []),
        "instructions": try_get(scraper.instructions_list, []),
        "totalTime": str(try_get(scraper.total_time, "")),
        "prepTime": str(try_get(scraper.prep_time, "")),
        "cooktime": str(try_get(scraper.cook_time, "")),
        "nutrition": try_get(scraper.nutrients, {}),
        "recipeYield": try_get(scraper.yields, ""),
        "review": try_get(lambda: scraper.reviews(), []),
        "recipeCategory": try_get(scraper.category, ""),
        "ratings": try_get(lambda: scraper.ratings(), ""),
        "recipeCuisine": try_get(scraper.cuisine, ""),
        "links": try_get(lambda: scraper.links(), []),
        "siteName": try_get(scraper.site_name, ""),
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


async def scrape_recipe(
    ctx: Context,
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    html: str | None,
) -> ScrapeResult:
    if not html:
        try:
            r = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            ctx.logger.error(f"{ctx.kv()} scrape_url={url} err={e} request failed")
            return ScrapeResult(url=url, data={}, error=e)
        ctx.logger.info(f"{ctx.kv()} scrape_url={url} status_code={r.status_code}")
        html = r.text
    else:
        ctx.logger.debug(f"{ctx.kv()} scrape_url={url} using html cache")

    scrape_result = None
    try:
        scrape_result = scrape_html(html, org_url=url, online=False, supported_only=False)
    except Exception as e:
        ctx.logger.error(f"{ctx.kv()} err={e} exception raised during scrape_html")
        return ScrapeResult(url=url, data={}, error=e)

    schema_data = None
    try:
        schema_data = to_schema_data(scrape_result)
    except Exception as e:
        return ScrapeResult(url=url, data={}, error=e)

    return ScrapeResult(url=url, data=schema_data, error=None)


async def scrape_urls(ctx: Context, jobs: list[ScrapeJob]) -> list[ScrapeResult]:
    async with httpx.AsyncClient() as client:
        tasks = [scrape_recipe(ctx, client, job.url.unicode_string(), __scrape_headers, job.html) for job in jobs]
        result = await asyncio.gather(*tasks)

    return result
