import html
import logging
from pprint import pprint
import re

import inflect
import nltk
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from pydantic import AnyHttpUrl, BaseModel
from quantulum3 import parser

from routes import crfpp
from routes.cleaner import clean
from routes.parser import ParseResponse
from routes.scraper import CleanedResponse, ScrapeResponse, scrape_urls

nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")

logging.basicConfig(
    # standard logging config
    format="[%(levelname)s] %(asctime)s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


app = FastAPI(
    title="Recipe API",
    description="A simple API for parsing recipes and ingredients.",
    version="0.4.2",
)


@app.get("/ready")
def ready():
    return {"status": "ok"}


class ScrapeRequest(BaseModel):
    urls: list[AnyHttpUrl]
    html: dict[AnyHttpUrl, str] = {}


@app.post("/api/v1/scrape", response_model=list[ScrapeResponse])
async def scrape_recipe(req: ScrapeRequest):
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(
            status_code=400, detail={"error": "No URLs or HTML provided."}
        )

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    return await scrape_urls(req.urls, req.html)


@app.post("/api/v1/scrape/clean", response_model=list[CleanedResponse])
async def scrape_recipe_clean(req: ScrapeRequest):
    if len(req.urls) == 0 and len(req.html) == 0:
        raise HTTPException(
            status_code=400, detail={"error": "No URLs or HTML provided."}
        )

    if len(req.urls) == 0:
        req.urls = list(req.html.keys())

    data = await scrape_urls(req.urls, req.html)

    for d in data:
        d.data = clean(d.data, d.url)

    return data


class ParseRequest(BaseModel):
    ingredients: list[str]


@app.post("/api/v1/parse", response_model=list[ParseResponse])
def parse_ingredients(ingredients: ParseRequest):
    return crfpp.convert_list_to_crf_model(ingredients.ingredients)


def normalize_string(string):
    # Convert all named and numeric character references (e.g. &gt;, &#62;)
    unescaped_string = html.unescape(string)
    return re.sub(
        r"\s+",
        " ",
        unescaped_string.replace("\xa0", " ")
        .replace("\n", " ")  # &nbsp;
        .replace("\t", " ")
        .strip(),
    )


p = inflect.engine()


def drop_adverbs_and_adjectives(ingredient: str) -> str:
    text = nltk.word_tokenize(ingredient)
    tagged = nltk.pos_tag(text)
    print(tagged)

    s = ""

    for word, tag in tagged:
        print(word, tag)
        if tag == "NNS":
            s += p.singular_noun(word)
            if s:
                s += " "
            else:
                s += word + " "
        elif tag != "VBD":
            s += word + " "

        print(s)

    return s.strip()


def normalize_ingredients(ingredients):
    n_ingredients = []
    for ingredient in ingredients:
        p_ing = parser.parse(normalize_string(ingredient))
        p_ing = p_ing[0] if len(p_ing) > 0 else None

        pprint(p_ing)

        parsed = ingredient
        if p_ing:
            u_name = p_ing.unit.name if p_ing.unit.name != "dimensionless" else ""

            parsed = parsed.replace(p_ing.surface, f"{p_ing.value} {u_name}", 1)
            parsed = drop_adverbs_and_adjectives(parsed)

        n_ingredients.append(
            {
                "original": ingredient,
                "inlined": parsed,
                "crfpp": crfpp.convert_list_to_crf_model([parsed])[0],
                "name": normalize_string(ingredient.replace(p_ing.surface, "", 1))
                if p_ing
                else ingredient,
                "quantity": p_ing.value if p_ing else None,
                "unit": p_ing.unit.name if p_ing else None,
            }
        )
    return n_ingredients


@app.post("/api/v2/parse", response_model=list)
def parse_ingredients_v2(ingredients: ParseRequest):
    return normalize_ingredients(ingredients.ingredients)
