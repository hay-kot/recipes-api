from pydantic import AnyHttpUrl, BaseModel, ConfigDict


class ScrapeRequest(BaseModel):
    urls: list[AnyHttpUrl]
    html: dict[AnyHttpUrl, str] = {}


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
    other: str = ""
    qty: float = 0.0
    comment: str = ""
    unit: str = ""
    confidence: ParseConfidence
