from starlette.applications import Starlette
from starlette.routing import Route

from core.parser import parse_ingredients
from core.scraper import scrape

app = Starlette(
    debug=True,
    routes=[
        Route("/scrape", scrape, methods=["POST"]),
        Route("/parse", parse_ingredients, methods=["POST"]),
    ],
)
