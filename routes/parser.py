from starlette.requests import Request
from starlette.responses import JSONResponse

from routes import crfpp


async def parse_ingredients(request: Request):
    """
    Parse a list of ingredients.
    """
    data = await request.json()
    ingredients: list[str] = data.get("ingredients")
    if not ingredients:
        return JSONResponse(
            {"error": "No ingredients provided."},
            status_code=400,
        )

    parsed_ingredients = crfpp.convert_list_to_crf_model(ingredients)
    return JSONResponse(
        [p.__dict__ for p in parsed_ingredients],
    )
