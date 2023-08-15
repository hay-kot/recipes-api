from pydantic import BaseModel, ConfigDict


class Confidence(BaseModel):
    qty: float = 0.0
    name: str = ""
    average: float = 0.0


class ParseResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    input: str
    name: str = ""
    other: str = ""
    qty: str = ""
    comment: str = ""
    unit: str = ""
    confidence: Confidence
