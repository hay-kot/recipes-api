from fractions import Fraction

from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import CompositeIngredientAmount
from pint import Unit
from quantulum3 import parser

from pkg.schema.scrapers import ParsedIngredients, ParsedNutrition
from pkg.schema.web import Context
from pkg.services.parser.pre_processor import normalize_ingredient, pre_process_string


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


def list_to_parsed_ingredients(ingredients: list[str], _: Context) -> list[ParsedIngredients]:
    parsed_ingredients: list[ParsedIngredients] = []

    for ingredient in ingredients:
        original_input = ingredient
        ingredient = pre_process_string(ingredient)
        ingredient = normalize_ingredient(ingredient)
        parsed_ingredient = parse_ingredient(ingredient)

        amount = None
        if parsed_ingredient.amount:
            amount = parsed_ingredient.amount[0]

        if isinstance(amount, CompositeIngredientAmount):
            composite_amount: CompositeIngredientAmount = amount
            amount = composite_amount.amounts[0]

        unit_str = ""
        if hasattr(amount, "unit"):
            if isinstance(amount.unit, str):
                unit_str = amount.unit
            elif isinstance(amount.unit, Unit):
                unit_str = amount.unit.__str__()

        comment = ""
        if parsed_ingredient.preparation:
            comment = parsed_ingredient.preparation.text
        elif parsed_ingredient.comment:
            comment = parsed_ingredient.comment.text

        parsed_ingredients.append(
            ParsedIngredients(
                input=original_input,
                name=parsed_ingredient.name.text if parsed_ingredient.name else "",
                qty=convert_to_float(amount.quantity) if amount else 1.0,
                unit=unit_str,
                confidence=amount.confidence if amount else 0.0,
                comment=comment,
                other="",
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
