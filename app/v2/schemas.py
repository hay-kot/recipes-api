from enum import Enum
from typing import Any

import httpx
from pydantic import AnyHttpUrl, BaseModel, ConfigDict
from recipe_scrapers import NoSchemaFoundInWildMode

from app.scraper.recipe import Recipe


class ParseRequest(BaseModel):
    ingredients: list[str]
    """ingredients is a list of strings to parse."""

class ParsedIngredients(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    input: str
    """input is the original input string"""

    name: str = ""
    """the parsed food/ingredient name"""

    qty: float = 0.0
    """the parsed quantity of the ingredient"""

    unit: str = ""
    """the parsed unit of the ingredient"""

    comment: str = ""
    """extra information about the quantity"""

    other: str = ""
    """extra information about the ingredient"""

class ScrapeError(str, Enum):
    unknown = 'unknown'
    """default error type"""

    unreachable = 'unreachable'
    """unreachable means the http endpoint is unreachable"""

    no_html_found = 'no_html_found'
    """no_html_found means the scraper could not find any html within the site"""

    no_schema_found = 'no_schema_found'
    """no_schema_found means the scraper could not find a schema within the side HTML"""

    def from_exception(e: Exception):
        if e is None:
            return None

        if isinstance(e, httpx.HTTPError):
            return ScrapeError.unreachable
        elif isinstance(e, NoSchemaFoundInWildMode):
            return ScrapeError.no_schema_found
        else:
            return ScrapeError.unknown


class ScrapeRequest(BaseModel):
    url: AnyHttpUrl
    """url is the url to scrape."""

    html: str | None = None
    """html is an optional field to prevent scraping the site and use the provided html instead."""

class CleanedScrapeResponse(BaseModel):
    url: AnyHttpUrl
    """url is the url that was scraped."""

    data: Recipe | None = None
    """data is the cleaned data returned from the scraper."""

    ingredients: list[ParsedIngredients] | None = None
    """parsed results of the ingredients"""

    error: ScrapeError | None = None
    """error is the error that occurred while scraping."""

class ScrapeResponse(BaseModel):
    url: AnyHttpUrl
    """url is the url that was scraped."""

    data: dict[str, Any] | None = None
    """data is the raw data returned from the scraper."""

    error: ScrapeError | None = None
    """error is the error that occurred while scraping."""