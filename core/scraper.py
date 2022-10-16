import asyncio

import httpx
from recipe_scrapers import scrape_html
from starlette.responses import JSONResponse

_FIREFOX_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"
)


async def get_html(urls: list[str]) -> list[str]:
    async with httpx.AsyncClient() as client:

        tasks = [client.get(url, headers={"User-Agent": _FIREFOX_UA}) for url in urls]
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
