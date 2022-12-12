from pydantic import BaseModel


class Confidence(BaseModel):
    qty: float
    name: float
    average: float


class ParseResponse(BaseModel):
    input: str
    name: str
    other: str
    qty: str
    comment: str
    unit: str
    confidence: Confidence
