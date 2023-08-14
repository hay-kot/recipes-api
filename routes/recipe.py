import datetime

from pydantic import BaseModel, Field


class Instructions(BaseModel):
    text: str


class Author(BaseModel):
    name: str
    url: str


class Recipe(BaseModel):
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
    totalTime: str | None = None

    dateModified: datetime.datetime | None = None
    datePublished: datetime.datetime | None = None
