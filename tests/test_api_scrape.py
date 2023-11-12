import json
import os
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.scraper.recipe import Recipe

CWD = pathlib.Path(__file__).parent

SNAPSHOT = os.environ.get("SNAPSHOT", False) in {"1", "true", "True"}


def readHTML(name: str) -> str:
    return CWD.joinpath("testdata", name).read_text()


def readRecipe(name: str) -> Recipe:
    js = json.loads(CWD.joinpath("testdata", name).read_text())
    return Recipe(**js)


def test_ready(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "url,name",
    [
        (
            "https://www.seriouseats.com/homemade-merguez-sausage-recipe",
            "homemade-merguez-sausage-recipe",
        ),
        (
            "https://www.bonappetit.com/recipe/pimento-cheese-crackers",
            "pimento-cheese-crackers",
        ),
    ],
)
def test_parse_clean(client: TestClient, url: str, name: str) -> None:
    resp = client.post(
        "/api/v1/scrape/clean",
        json={"urls": [], "html": {url: readHTML(name + ".html")}},
    )

    expect = readRecipe(name + ".json")

    assert resp.status_code == 200

    data: list[dict] = resp.json()

    assert len(data) == 1

    first = data[0]

    assert first["url"] == url

    recipe = Recipe(**first["data"])

    if SNAPSHOT:
        snapshot = CWD / "snapshots" / (name + ".json")
        snapshot.parent.mkdir(parents=True, exist_ok=True)

        with snapshot.open("w") as f:
            f.write(json.dumps(first["data"], indent=2))

    assert recipe.name == expect.name
    assert recipe.url == expect.url
    assert recipe.description == expect.description

    for i, j in zip(recipe.instructions, expect.instructions):
        assert i.text == j.text

    assert recipe.ingredients == expect.ingredients
    assert recipe.category == expect.category

    assert recipe.keywords == expect.keywords
    assert recipe.images == expect.images

    assert recipe.recipeYield == expect.recipeYield
    assert recipe.prepTime == expect.prepTime
    assert recipe.performTime == expect.performTime
    assert recipe.totalTime == expect.totalTime

    assert recipe.dateModified == expect.dateModified
    assert recipe.datePublished == expect.datePublished

    assert recipe.recipeCuisine == expect.recipeCuisine
