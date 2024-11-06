from typing import Annotated

from fastapi import APIRouter, Depends

from pkg.schema import scrapers as schema
from pkg.schema.web import Context
from pkg.services.parser.nlp_parser import list_to_parsed_ingredients

router = APIRouter(prefix="/processors", tags=["Processors"])


@router.post("/ingredients", response_model=list[schema.ParsedIngredients])
def process_ingredients(ctx: Annotated[Context, Depends(Context)], ingredients: schema.ParseRequest):
    """
    The Process Ingredients endpoint will turn unstructured recipes into a
    structured array of parsed ingredients using a NLP Parser that has been
    trained to identify part of ingredients.
    """
    return list_to_parsed_ingredients(ingredients.ingredients, ctx)
