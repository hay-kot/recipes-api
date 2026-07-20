import re
from fractions import Fraction

from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import CompositeIngredientAmount
from pint import Unit

from pkg.schema.scrapers import ParsedIngredients, ParsedNutrition
from pkg.schema.web import Context
from pkg.services.parser.pre_processor import pre_process_string

_MASS_DIMENSIONALITY = Unit("gram").dimensionality

# Deterministic unit canonicalisation. ingredient-parser already returns a
# pint.Unit (canonical singular) for units it recognises; this only kicks in for
# the string units it leaves as-is (e.g. a plural/capitalised "Tablespoons" the
# CRF emitted that pint couldn't parse). This replaces the quantulum3 normalize
# step, which cost ~half the per-line latency, dragged in scikit-learn+scipy,
# and mangled ~1-in-7 lines. Unknown units pass through unchanged.
_UNIT_ALIASES = {
    "tablespoon": "tablespoon",
    "tablespoons": "tablespoon",
    "tbsp": "tablespoon",
    "tbsps": "tablespoon",
    "tbs": "tablespoon",
    "tbl": "tablespoon",
    "teaspoon": "teaspoon",
    "teaspoons": "teaspoon",
    "tsp": "teaspoon",
    "tsps": "teaspoon",
    "cup": "cup",
    "cups": "cup",
    "gram": "gram",
    "grams": "gram",
    "g": "gram",
    "gramme": "gram",
    "grammes": "gram",
    "kilogram": "kilogram",
    "kilograms": "kilogram",
    "kg": "kilogram",
    "milligram": "milligram",
    "milligrams": "milligram",
    "mg": "milligram",
    "ounce": "ounce",
    "ounces": "ounce",
    "oz": "ounce",
    "ozs": "ounce",
    "pound": "pound",
    "pounds": "pound",
    "lb": "pound",
    "lbs": "pound",
    "milliliter": "milliliter",
    "milliliters": "milliliter",
    "millilitre": "milliliter",
    "millilitres": "milliliter",
    "ml": "milliliter",
    "liter": "liter",
    "liters": "liter",
    "litre": "liter",
    "litres": "liter",
    "pint": "pint",
    "pints": "pint",
    "quart": "quart",
    "quarts": "quart",
    "gallon": "gallon",
    "gallons": "gallon",
}


def canonicalize_unit(unit: str) -> str:
    """Map a unit surface form to a canonical singular name; pass through unknowns."""
    if not unit:
        return ""
    key = unit.strip().rstrip(".").lower()
    return _UNIT_ALIASES.get(key, unit)


# Nutrition values are almost always "<number> <unit>" (e.g. "6 grams", "110 mg").
# This regex-based parser replaces quantulum3 without the ML dependency. Energy
# units (Calories/calories/kcal) all normalise to "calorie" — consistent with the
# full-word "gram"/"milligram" and how nutrition is commonly labelled.
_NUTRITION_NUMBER_UNIT = re.compile(r"(-?\d+(?:\.\d+)?)\s*([A-Za-z]+)")
_NUTRITION_UNITS = {
    "g": "gram",
    "gram": "gram",
    "grams": "gram",
    "gramme": "gram",
    "grammes": "gram",
    "mg": "milligram",
    "milligram": "milligram",
    "milligrams": "milligram",
    "mcg": "microgram",
    "microgram": "microgram",
    "micrograms": "microgram",
    "kg": "kilogram",
    "kilogram": "kilogram",
    "kilograms": "kilogram",
    "cup": "cup",
    "cups": "cup",
    "ml": "milliliter",
    "milliliter": "milliliter",
    "milliliters": "milliliter",
    "l": "liter",
    "liter": "liter",
    "liters": "liter",
    "litre": "liter",
    "litres": "liter",
    "kcal": "calorie",
    "cal": "calorie",
    "calorie": "calorie",
    "calories": "calorie",
}


def _nutrition_unit(token: str) -> str | None:
    return _NUTRITION_UNITS.get(token.lower())


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

    for name, value in nutrition.items():
        if not isinstance(value, str):
            continue

        # Take the first "<number> <unit>" pair, matching quantulum's use of the
        # most-likely (first) entity. A bare number ("399") or an unrecognised
        # unit ("1 serving") yields nothing, as before.
        match = _NUTRITION_NUMBER_UNIT.search(value)
        if not match:
            continue

        unit = _nutrition_unit(match.group(2))
        if unit is None:
            continue

        parsed_nutrition.append(
            ParsedNutrition(
                name=name,
                amount=float(match.group(1)),
                unit=unit,
            )
        )

    return parsed_nutrition


def list_to_parsed_ingredients(ingredients: list[str], _: Context) -> list[ParsedIngredients]:
    parsed_ingredients: list[ParsedIngredients] = []

    for ingredient in ingredients:
        original_input = ingredient
        ingredient = pre_process_string(ingredient)
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
        unit_str = canonicalize_unit(unit_str)

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
                qty=round(convert_to_float(amount.quantity), 3) if amount else 1.0,
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
