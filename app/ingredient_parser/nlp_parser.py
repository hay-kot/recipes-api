from fractions import Fraction

from ingredient_parser import parse_ingredient
from quantulum3 import parser

from app.ingredient_parser.crfpp.pre_processor import pre_process_string
from app.v2.schemas import ParsedIngredients, ParsedNutrition


def dict_to_parsed_nutrition(nutrition: dict[str, str]) -> list[ParsedNutrition]:
    parsed_nutrition: list[ParsedNutrition] = []

    for key, value in nutrition.items():
        name = key

        try:
            parsed = parser.parse(value)
        except Exception:
            continue

        # use the first entry in the parsed list as the most likely

        if len(parsed) == 0:
            continue

        entity = parsed[0]

        if entity.unit is not None and entity.unit.name != "dimensionless":
            parsed_nutrition.append(
                ParsedNutrition(
                    name=name,
                    amount=entity.value,
                    unit=entity.unit.name,
                )
            )

    return parsed_nutrition


def list_to_parsed_ingredients(ingredients: list[str]) -> list[ParsedIngredients]:
    parsed_ingredients: list[ParsedIngredients] = []

    for ingredient in ingredients:
        ingredient = pre_process_string(ingredient)
        parsed_ingredient = parse_ingredient(ingredient)

        amount = None
        if parsed_ingredient.amount:
            amount = parsed_ingredient.amount[0]

        comment = ""
        if parsed_ingredient.preparation:
            comment = parsed_ingredient.preparation.text
        elif parsed_ingredient.comment:
            comment = parsed_ingredient.comment.text

        parsed_ingredients.append(
            ParsedIngredients(
                input=ingredient,
                name=parsed_ingredient.name.text if parsed_ingredient.name else "",
                qty=convert_to_float(amount.quantity) if amount else 1.0,
                unit=amount.unit if amount else "",
                confidence=amount.confidence if amount else 0.0,
                comment=comment,
                other=parsed_ingredient.other.text if parsed_ingredient.other else "",
            )
        )

    return parsed_ingredients


def convert_to_float(frac_str: str | float):
    if frac_str is None:
        return 1.0

    if isinstance(frac_str, float):
        return frac_str
    if isinstance(frac_str, int):
        return float(frac_str)
    if isinstance(frac_str, str):
        # some format as 1-1/2 cups water
        frac_str = frac_str.replace("-", " ")

        try:
            return float(sum(Fraction(s) for s in frac_str.split()))
        except ValueError:
            return 1.0
