import json
import pathlib

from recipe_scrapers import scrape_html

# importing the service module applies the lxml parser patch
import pkg.services.recipes.scraper  # noqa: F401
from pkg.services.recipes.scraper import to_ingredient_groups

_TESTDATA = pathlib.Path(__file__).resolve().parent.parent / "endpoint" / "testdata"

_HTML = (_TESTDATA / "sallysbakingaddiction.com__spinach-bacon-breakfast-strata.html").read_text()


def scrape_fixture(name: str, url: str):
    return scrape_html((_TESTDATA / name).read_text(), org_url=url, online=False, supported_only=False)


def test_scraper_uses_lxml_not_html_parser() -> None:
    """Guard the perf patch: the main page soup must be built with lxml, not the
    hardcoded pure-Python html.parser. If recipe_scrapers changes such that the
    patch stops taking effect, scraping still works but we lose the speedup —
    this test catches that silently regressing."""
    scraper = scrape_html(_HTML, org_url="https://example.com", online=False, supported_only=False)
    assert scraper.soup.builder.NAME == "lxml"
    # sanity: extraction still works
    assert scraper.title()


def test_ingredient_groups_captures_headings() -> None:
    scraper = scrape_fixture(
        "pinchofyum.com__spicy-shrimp-tacos-with-garlic-cilantro-lime-slaw.html",
        "https://pinchofyum.com/spicy-shrimp-tacos-with-garlic-cilantro-lime-slaw",
    )

    groups = to_ingredient_groups(scraper)

    assert groups is not None
    assert [group["purpose"] for group in groups] == [
        "Garlic Cilantro Lime Sauce:",
        "Shrimp Taco Spice Mix:",
        "Stuff for the Shrimp Tacos:",
    ]
    assert [ingredient for group in groups for ingredient in group["ingredients"]] == scraper.ingredients()


def test_ingredient_groups_dropped_when_page_has_no_headings() -> None:
    scraper = scrape_fixture(
        "sallysbakingaddiction.com__spinach-bacon-breakfast-strata.html",
        "https://sallysbakingaddiction.com/spinach-bacon-breakfast-strata",
    )

    assert to_ingredient_groups(scraper) is None


def wprm_page(rows: list[tuple[str | None, list[str]]]) -> str:
    """Build a page in the WPRM shape recipe_scrapers auto-detects: schema.org
    ingredients in document order, plus the markup the headings are read from."""
    ingredients = [ingredient for _, group in rows for ingredient in group]

    markup = ""
    for heading, group in rows:
        if heading is not None:
            markup += f'<h4 class="wprm-recipe-group-name">{heading}</h4>'
        for ingredient in group:
            markup += f'<li class="wprm-recipe-ingredient">{ingredient}</li>'

    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Test Recipe",
        "recipeIngredient": ingredients,
        "recipeInstructions": [{"@type": "HowToStep", "text": "Cook it."}],
    }

    return (
        f'<html><head><script type="application/ld+json">{json.dumps(schema)}</script></head>'
        f'<body><div class="wprm-recipe-ingredient-group">{markup}</div></body></html>'
    )


def test_ingredient_groups_kept_when_headings_are_distinct() -> None:
    scraper = scrape_html(
        wprm_page([("For the Sauce", ["1 cup soy sauce", "2 tbsp honey"]), ("For the Slaw", ["1 head cabbage"])]),
        org_url="https://example.com",
        online=False,
        supported_only=False,
    )

    groups = to_ingredient_groups(scraper)

    assert groups is not None
    assert [group["purpose"] for group in groups] == ["For the Sauce", "For the Slaw"]


def test_ingredient_groups_dropped_when_a_repeated_heading_reorders_them() -> None:
    """recipe_scrapers buckets groups by heading text, so a heading that appears twice
    merges into its first occurrence and the groups stop following page order while
    keeping their total length. Membership downstream is positional, so accepting this
    would file the slaw ingredients under "For the Sauce"."""
    scraper = scrape_html(
        wprm_page(
            [
                ("For the Sauce", ["1 cup soy sauce", "2 tbsp honey"]),
                ("For the Slaw", ["1 head cabbage", "1 carrot"]),
                ("For the Sauce", ["1 lime", "1 tsp salt"]),
            ]
        ),
        org_url="https://example.com",
        online=False,
        supported_only=False,
    )

    # precondition: the library really does hand back a reordered, same-length grouping
    groups = scraper.ingredient_groups()
    assert [ingredient for group in groups for ingredient in group.ingredients] != scraper.ingredients()
    assert sum(len(group.ingredients) for group in groups) == len(scraper.ingredients())

    assert to_ingredient_groups(scraper) is None


def test_ingredient_groups_dropped_when_a_blank_heading_reorders_them() -> None:
    """A heading whose text normalizes to empty collapses onto the same key as the
    leading unnamed block, merging trailing ingredients backwards into it."""
    scraper = scrape_html(
        wprm_page(
            [
                (None, ["1 cup flour", "2 eggs"]),
                ("For the Sauce", ["3 tbsp butter", "4 cloves garlic"]),
                ("&nbsp;", ["5 sprigs thyme"]),
            ]
        ),
        org_url="https://example.com",
        online=False,
        supported_only=False,
    )

    assert to_ingredient_groups(scraper) is None
