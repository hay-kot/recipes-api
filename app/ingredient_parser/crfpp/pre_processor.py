import re
import unicodedata
from fractions import Fraction

from quantulum3 import parser

replace_abbreviations = {
    "cup": " cup ",
    "g": " gram ",
    "kg": " kilogram ",
    "lb": " pound ",
    "ml": " milliliter ",
    "oz": " ounce ",
    "pint": " pint ",
    "qt": " quart ",
    "tbsp": " tablespoon ",
    "tbs": " tablespoon ",  # Order Matters!, 'tsb' must come after 'tbsp' in case of duplicate matches
    "tsp": " teaspoon ",
}


def replace_invisible_whitespace(text):
    # Define a list of invisible whitespace characters
    invisible_whitespace_chars = ["\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\u2060", "\u3000"]

    # Replace invisible whitespace characters with normal whitespace
    for char in invisible_whitespace_chars:
        text = text.replace(char, " ")

    return text


def replace_common_abbreviations(string: str) -> str:
    for k, v in replace_abbreviations.items():
        regex = rf"(?<=\d)\s?({k}\bs?)"
        string = re.sub(regex, v, string)

    return string


def remove_periods(string: str) -> str:
    """Removes periods not sournded by digets"""
    return re.sub(r"(?<!\d)\.(?!\d)", "", string)


def replace_fraction_unicode(string: str):
    # TODO: I'm not confident this works well enough for production needs some testing and/or refacorting
    # TODO: Breaks on multiple unicode fractions
    for c in string:
        try:
            name = unicodedata.name(c)
        except ValueError:
            continue
        if name.startswith("VULGAR FRACTION"):
            normalized = unicodedata.normalize("NFKC", c)
            numerator, _, denominator = normalized.partition("⁄")  # _ = slash
            text = f" {numerator}/{denominator}"
            return string.replace(c, text).replace("  ", " ")

    return string


def wrap_or_clause(string: str):
    """
    Attempts to wrap or clauses in ()

    Examples:
    '1 tsp. Diamond Crystal or ½ tsp. Morton kosher salt, plus more'
        -> '1 teaspoon diamond crystal (or 1/2 teaspoon morton kosher salt), plus more'

    """
    # TODO: Needs more adequite testing to be sure this doesn't have side effects.
    split_by_or = string.split(" or ")

    split_by_comma = split_by_or[1].split(",")

    if len(split_by_comma) > 0:
        return f"{split_by_or[0]} (or {split_by_comma[0]}),{''.join(split_by_comma[1:])}".strip().removesuffix(",")

    return string


def normalize_ingredient(string: str) -> str:
    string = pre_process_string(string)

    parsed = None
    try:
        parsed = parser.parse(string)
    except Exception:
        return string

    # Replace identified units and quantities with their normalized values
    for entity in parsed:
        if entity.unit is not None and entity.unit.name != "dimensionless":
            if entity.surface:
                unit: str = entity.unit.name
                if unit.endswith("-mass"):
                    unit = unit.removesuffix("-mass")
                elif unit == "cubic centimetre":
                    # ml is parsed as cubic centimetre
                    unit = "milliliter"

                # in some cases a fraction is a better representation of the quantity
                # than the float value. This has to do with how crfpp handles fractions
                rounded = round(entity.value, 3)
                quantityStr = str(rounded)
                if unit == "teaspoon" or unit == "tablespoon" or rounded < 0:
                    quantityStr = fraction_str(rounded)

                string = string.replace(entity.surface, f"{quantityStr} {unit}")

    return string


def fraction_str(num: float) -> str:
    """
    Converts a float to a fraction string if possible. Otherwise returns the original float as a string.

    Examples:
    1.5 -> '1 1/2'
    1.333 -> '1 1/3'
    1.25 -> '1 1/4'
    1.0 -> '1'
    1.1 -> '1.1'
    """
    if num.is_integer():
        return str(int(num))
    else:
        frac = Fraction(num).limit_denominator()
        if frac.numerator == 1:
            return f"{frac.numerator}/{frac.denominator}"
        else:
            whole_part = int(num)
            fractional_part = frac - whole_part

            if whole_part == 0:
                return f"{fractional_part.numerator}/{fractional_part.denominator}"

            return f"{whole_part} {fractional_part.numerator}/{fractional_part.denominator}"


def pre_process_string(string: str) -> str:
    """
    Series of preprocessing functions to make best use of the CRF++ model. The ideal string looks something like...

    {qty} {unit} {food}, {additional}
    1 tbs. wine, expensive or other white wine, plus more

    """
    # string = string.lower()
    string = replace_invisible_whitespace(string)
    string = replace_fraction_unicode(string)
    string = remove_periods(string)
    string = replace_common_abbreviations(string)

    # if " or " in string:
    #     string = wrap_or_clause(string)

    # Remove duplicate whitespace
    string = " ".join(string.split())

    return string
