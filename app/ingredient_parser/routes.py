from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from . import crfpp


class ParseRequest(BaseModel):
    ingredients: list[str]


class ParseConfidence(BaseModel):
    qty: float = 0.0
    name: str = ""
    average: float = 0.0


class ParseResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    input: str
    name: str = ""
    qty: float = 0.0
    comment: str = ""
    unit: str = ""
    confidence: ParseConfidence


router = APIRouter(tags=["Ingredient Parser"])


@router.post("/v1/parse", response_model=list[ParseResponse])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)
