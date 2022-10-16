from starlette.applications import Starlette
from starlette.routing import Route

from routes.parser import parse_ingredients
from routes.scraper import scrape

app = Starlette(
    debug=True,
    routes=[
        Route("/scrape", scrape, methods=["POST"]),
        Route("/parse", parse_ingredients, methods=["POST"]),
    ],
)
