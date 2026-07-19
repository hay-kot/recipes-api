from fractions import Fraction

from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import CompositeIngredientAmount
from pint import Unit
from quantulum3 import parser

from pkg.schema.scrapers import ParsedIngredients, ParsedNutrition
from pkg.schema.web import Context
from pkg.services.parser.pre_processor import normalize_ingredient, pre_process_string

_MASS_DIMENSIONALITY = Unit("gram").dimensionality

# A count unit is only overridden by a weight when the parser is genuinely
# unsure about it. Deliberate counts ("4 breasts", "1 can") score ~1.0; the
# spurious defaults we want to replace score well below this.
_COUNT_CONFIDENCE_CEILING = 0.9


def _is_mass_unit(unit) -> bool:
    return isinstance(unit, Unit) and unit.dimensionality == _MASS_DIMENSIONALITY


def _is_count_amount(amount) -> bool:
    """True when the amount's unit is a bare count (e.g. "slice", "can") rather
    than a dimensioned measure such as a weight or volume."""
    unit = getattr(amount, "unit", None)
    if unit is None:
        return False
    return not isinstance(unit, Unit) or unit.dimensionless


def select_amount(amounts):
    """Pick the amount that best represents the ingredient quantity.

    ingredient-parser v2 sometimes ranks a low-confidence count unit ahead of an
    explicit weight (e.g. "10 ounces ... slices" -> "1 slice"). When the primary
    amount is such an uncertain count and a more confident weight is present,
    prefer the weight. Deliberate counts ("4 chicken breasts", "1 can") keep
    their count because they score above the confidence ceiling.
    """
    if not amounts:
        return None

    primary = amounts[0]
    if _is_count_amount(primary) and primary.confidence < _COUNT_CONFIDENCE_CEILING:
        weight = next(
            (a for a in amounts if _is_mass_unit(getattr(a, "unit", None)) and a.confidence > primary.confidence),
            None,
        )
        if weight is not None:
            return weight

    return primary


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

        amount = select_amount(parsed_ingredient.amount)

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

        # ingredient-parser v2 returns name as a list of IngredientText segments
        name = ", ".join(n.text for n in parsed_ingredient.name) if parsed_ingredient.name else ""

        parsed_ingredients.append(
            ParsedIngredients(
                input=original_input,
                name=name,
                qty=convert_to_float(amount.quantity) if amount else 1.0,
                unit=unit_str,
                confidence=amount.confidence if amount else 0.0,
                comment=comment,
                other="",
            )
        )

    return parsed_ingredients


def convert_to_float(frac_str: str | float | Fraction):
    if frac_str is None:
        return 1.0

    # ingredient-parser v2 returns quantities as Fraction instances
    if isinstance(frac_str, Fraction):
        return float(frac_str)
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
