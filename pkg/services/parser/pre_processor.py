import re
import unicodedata

replace_abbreviations = {
    "cup": " cup ",
    " c ": " cup ",
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

        regex = rf"(?<=\d)\s?({k.upper()}\bs?)"
        string = re.sub(regex, v, string)

    return string


def remove_periods(string: str) -> str:
    """Removes periods not sournded by digets"""
    return re.sub(r"(?<!\d)\.(?!\d)", "", string)


def normalize_mixed_number(string: str) -> str:
    """Rewrites a hyphenated mixed number to its space-separated form.

    Recipes commonly write "one and a half" as "1-1/2". ingredient-parser reads
    the hyphen as a range (0.5 to 1) instead, so normalize "1-1/2" -> "1 1/2".
    Genuine ranges ("3-4", "1/2-1", "1 1/2-2") are left untouched because a whole
    number followed by a fraction is never a valid ascending range.
    """
    return re.sub(r"(?<![\d/])(\d+)-(\d+/\d+)", r"\1 \2", string)


def normalize_inch_marks(string: str) -> str:
    """Rewrite an inch mark glued to a number ('1/2"') as ' inch'.

    A quote glued directly to a fraction (e.g. cut into 1/2" pieces) trips up
    ingredient-parser's fraction tokenisation and leaks its internal '#1$2'
    sentinel into the output. Expanding it to ' inch' also reads better.
    """
    return re.sub(r'(?<=[0-9])\s?["”″]', " inch ", string)


def replace_fraction_unicode(string: str):
    """Expand every vulgar fraction char (½, ¼, ¾, ⅔, ...) to ' n/d'.

    The leading space separates a whole number glued to the fraction
    ("1½" -> "1 1/2"). All occurrences are handled (a sentence can contain more
    than one, e.g. "1¼ lb ... cut into ½ inch").
    """
    out = []
    for c in string:
        try:
            name = unicodedata.name(c)
        except ValueError:
            out.append(c)
            continue
        if name.startswith("VULGAR FRACTION"):
            numerator, _, denominator = unicodedata.normalize("NFKC", c).partition("⁄")
            out.append(f" {numerator}/{denominator}")
        else:
            out.append(c)

    return "".join(out)


def pre_process_string(string: str) -> str:
    """
    Series of preprocessing functions to make best use of the CRF++ model. The ideal string looks something like...

    {qty} {unit} {food}, {additional}
    1 tbs. wine, expensive or other white wine, plus more

    """
    # string = string.lower()
    string = replace_invisible_whitespace(string)
    string = replace_fraction_unicode(string)
    string = normalize_inch_marks(string)
    string = normalize_mixed_number(string)
    string = remove_periods(string)
    string = replace_common_abbreviations(string)

    # Remove duplicate whitespace
    string = " ".join(string.split())

    return string
