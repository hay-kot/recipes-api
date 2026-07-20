import sys

# importing pkg runs slim_extruct() (see pkg/__init__.py)
import pkg  # noqa: F401
from pkg.services.recipes.scraper import scrape_html, to_schema_data


def test_heavy_extruct_extractors_are_not_imported() -> None:
    """recipe_scrapers only asks extruct for json-ld + microdata, so the
    microformat (mf2py) and RDFa (pyRdfa -> rdflib) extractors must never load.
    Guards the ~16 MiB floor saving against a regression."""
    assert sys.modules.get("extruct.microformat", None) is not None
    assert getattr(sys.modules["extruct.microformat"], "__extruct_stub__", False) is True
    assert getattr(sys.modules["extruct.rdfa"], "__extruct_stub__", False) is True
    for heavy in ("mf2py", "rdflib", "pyRdfa"):
        assert heavy not in sys.modules, f"{heavy} should not be imported"


def test_scraping_still_works_with_slim_extruct() -> None:
    scraper = scrape_html(
        "<html><head><script type='application/ld+json'>"
        '{"@context":"https://schema.org","@type":"Recipe","name":"Test",'
        '"recipeIngredient":["1 cup flour","2 eggs"]}'
        "</script></head><body></body></html>",
        org_url="https://example.com",
        online=False,
        supported_only=False,
    )
    data = to_schema_data(scraper)
    assert data.get("name") == "Test"
    assert len(data.get("ingredients", [])) == 2
