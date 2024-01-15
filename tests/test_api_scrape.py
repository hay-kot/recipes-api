import json
import os
import pathlib

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.scraper.recipe import Recipe

__filepath = pathlib.Path(__file__).parent

SNAPSHOT = os.environ.get("SNAPSHOT", False) in {"1", "true", "True"}


def read_recipe_html(name: str) -> str:
    return __filepath.joinpath("testdata", name).read_text()


def read_recipe_json(name: str) -> Recipe:
    js = json.loads(__filepath.joinpath("testdata", name).read_text())
    return Recipe(**js)


def test_ready(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200


def test_parse_clean_v2_errors(client: TestClient) -> None:
    resp = client.post(
        "/api/v2/scrape/clean",
        json=[
            {
                "url": "https://example.com",
                "html": "<html><body><h1>hello</h1></body></html>",
            },
        ],
    )

    assert resp.status_code == 200

    data: list[dict] = resp.json()

    assert len(data) == 1

    first = data[0]

    assert first["url"] == "https://example.com/"

    error = first["error"]

    assert error == "no_schema_found"




def load_test_cases() -> list[tuple[str, str]]:
    test_cases = []

    for path in __filepath.joinpath("testdata").glob("*.html"):
        html = path.read_text()

        soup = BeautifulSoup(html, "html.parser")

        # get canonical url
        canonical = soup.find("link", {"rel": "canonical"})

        if canonical:
            href = canonical.get("href")
            test_cases.append((href, path.stem))

    return test_cases


@pytest.mark.parametrize(
    "url,name",
    load_test_cases(),
)
def test_parse_clean_v2(client: TestClient, url: str, name: str) -> None:
    resp = client.post(
        "/api/v2/scrape/clean",
        json=[
            {"url": url, "html": read_recipe_html(name + ".html")},
        ],
    )

    assert resp.status_code == 200

    data: list[dict] = resp.json()

    assert len(data) == 1

    first = data[0]

    assert first["url"] == url

    recipe = Recipe(**first["data"])

    if SNAPSHOT:
        snapshot = __filepath / "snapshots" / (name + ".json")
        snapshot.parent.mkdir(parents=True, exist_ok=True)

        with snapshot.open("w") as f:
            f.write(json.dumps(first["data"], indent=2))

    expect = read_recipe_json(name + ".json")

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
