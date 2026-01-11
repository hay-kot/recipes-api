import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class Instructions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    text: str


class Author(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    url: str


def clean_date(date: Any) -> Any:
    if date is None:
        return None

    if isinstance(date, str):
        # some include EST or EDT at the end
        date = date.split(" ")[0]

        # if the string is too short or invalid, return None
        if len(date) < 8:  # minimum valid date is YYYY-M-D (8 chars)
            return None

    if isinstance(date, datetime.datetime):
        return date.date()

    return date


DateLike = Annotated[datetime.date | datetime.datetime | None, BeforeValidator(clean_date)]


class Recipe(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        coerce_numbers_to_str=True,
        strict=False,
    )

    name: str
    url: str
    description: str
    instructions: list[Instructions] = Field(
        default_factory=list,
        alias="recipeInstructions",
    )
    ingredients: list[str] = Field(
        default_factory=list,
        alias="recipeIngredient",
    )

    recipeCuisine: str | None = None
    category: list[str] = Field(default_factory=list, alias="recipeCategory")
    keywords: list[str] = []

    images: str | None | list[str]

    recipeYield: str | None = None

    prepTime: str | None = None
    performTime: str | None = None
    cookTime: str | None = None
    totalTime: str | None = None

    dateModified: DateLike | None = None
    datePublished: DateLike | None = None

    nutrition: dict[str, str] | None = Field(default_factory=dict)
