import asyncio

import httpx
from recipe_scrapers import scrape_html
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def get_html(urls: list[str]) -> list[str]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        result: list[httpx.Response] = await asyncio.gather(*tasks)

    return [r.text for r in result]


async def scrape(request):
    body = await request.json()

    url: list[str] = body.get("urls")

    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)

    if len(url) > 10:
        return JSONResponse(
            {"error": "too many urls, max 10 per request"}, status_code=400
        )

    htmls = await get_html(url)
    results = [scrape_html(html).schema.data for html in htmls]

    return JSONResponse(results)


async def homepage(request):
    return JSONResponse({"hello": "world"})


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/scrape", scrape, methods=["POST"]),
    ],
)
