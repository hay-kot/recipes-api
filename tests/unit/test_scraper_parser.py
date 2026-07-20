import pathlib

from recipe_scrapers import scrape_html

# importing the service module applies the lxml parser patch
import pkg.services.recipes.scraper  # noqa: F401

_HTML = (
    pathlib.Path(__file__).resolve().parent.parent
    / "endpoint"
    / "testdata"
    / "sallysbakingaddiction.com__spinach-bacon-breakfast-strata.html"
).read_text()


def test_scraper_uses_lxml_not_html_parser() -> None:
    """Guard the perf patch: the main page soup must be built with lxml, not the
    hardcoded pure-Python html.parser. If recipe_scrapers changes such that the
    patch stops taking effect, scraping still works but we lose the speedup —
    this test catches that silently regressing."""
    scraper = scrape_html(_HTML, org_url="https://example.com", online=False, supported_only=False)
    assert scraper.soup.builder.NAME == "lxml"
    # sanity: extraction still works
    assert scraper.title()
