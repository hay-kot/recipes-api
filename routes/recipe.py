import datetime

from pydantic import BaseModel, Field


class Instructions(BaseModel):
    text: str


class Author(BaseModel):
    name: str
    url: str


class Recipe(BaseModel):
    name: str
    url: str = Field(alias="orgUrl")
    description: str
    instructions: list[Instructions] = Field(
        default_factory=list,
        alias="recipeInstructions",
    )
    ingredients: list[str] = Field(
        default_factory=list,
        alias="recipeIngredient",
    )

    category: list[str] = Field(default_factory=list, alias="recipeCategory")

    keywords: list[str] = []

    images: str | None | list[str]

    recipeYield: str | None

    prepTime: str | None
    performTime: str | None
    totalTime: str | None

    dateModified: datetime.datetime | None
    datePublished: datetime.datetime | None
