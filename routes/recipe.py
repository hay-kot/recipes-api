import datetime

from pydantic import BaseModel, Field


class Instructions(BaseModel):
    text: str


class Author(BaseModel):
    name: str
    url: str


class Recipe(BaseModel):
    name: str
    description: str
    instructions: list[Instructions] = Field(
        default_factory=list,
        alias="recipeInstructions",
    )
    ingredients: list[str] = Field(
        default_factory=list,
        alias="recipeIngredient",
    )

    category: str | None
    keywords: list[str] = []

    images: str | None | list[str]

    recipeYield: str

    prepTime: str | None
    performTime: str | None
    totalTime: str | None

    dateModified: datetime.datetime | None
    datePublished: datetime.datetime | None
