import json
import os
import pathlib

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.scraper.recipe import Recipe
from app.v2.schemas import CleanedScrapeResponse

__filepath = pathlib.Path(__file__).parent

SNAPSHOT = os.environ.get("SNAPSHOT", False) in {"1", "true", "True"}


def read_recipe_html(name: str) -> str:
    return __filepath.joinpath("testdata", name).read_text()


def read_recipe_json(name: str) -> CleanedScrapeResponse:
    js = json.loads(__filepath.joinpath("testdata", name).read_text())
    return CleanedScrapeResponse(**js)


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
            f.write(json.dumps(first, indent=2))

    expect = read_recipe_json(name + ".json")
    expect_recipe = expect.data

    assert recipe.name == expect_recipe.name
    assert recipe.url == expect_recipe.url
    assert recipe.description == expect_recipe.description

    for i, j in zip(recipe.instructions, expect_recipe.instructions):
        assert i.text == j.text

    assert recipe.ingredients == expect_recipe.ingredients
    assert recipe.category == expect_recipe.category

    assert recipe.keywords == expect_recipe.keywords
    assert recipe.images == expect_recipe.images

    assert recipe.recipeYield == expect_recipe.recipeYield
    assert recipe.prepTime == expect_recipe.prepTime
    assert recipe.performTime == expect_recipe.performTime
    assert recipe.totalTime == expect_recipe.totalTime

    assert recipe.dateModified == expect_recipe.dateModified
    assert recipe.datePublished == expect_recipe.datePublished

    assert recipe.recipeCuisine == expect_recipe.recipeCuisine

    props = {"name", "amount", "unit"}
    for got, expt in zip(first["nutrition"], expect.nutrition):
        for prop in props:
            assert got[prop] == getattr(expt, prop)

    props = {"input", "name", "qty", "unit", "comment", "other", "confidence"}
    for got, expt in zip(first["ingredients"], expect.ingredients):
        for prop in props:
            if props == "qty" or props == "confidence":
                assert got[prop] == pytest.approx(getattr(expt, prop), rel=0.01)
                continue

            assert got[prop] == getattr(expt, prop)
