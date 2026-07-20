from dataclasses import dataclass

import pytest
from pytest import mark

from pkg.schema.web import Context
from pkg.services.parser.nlp_parser import canonicalize_unit, list_to_parsed_ingredients


@mark.parametrize(
    "surface,expect",
    [
        ("Tablespoons", "tablespoon"),
        ("Tbsp", "tablespoon"),
        ("Tbsp.", "tablespoon"),
        ("tbsp", "tablespoon"),
        ("tsp", "teaspoon"),
        ("cups", "cup"),
        ("grams", "gram"),
        ("g", "gram"),
        ("oz", "ounce"),
        ("lbs", "pound"),
        ("ml", "milliliter"),
        # already-canonical (pint) names pass through unchanged
        ("tablespoon", "tablespoon"),
        ("gram", "gram"),
        # count units and unknowns are preserved verbatim (quantulum never
        # canonicalised these either, so we don't gratuitously singularise them)
        ("cloves", "cloves"),
        ("slices", "slices"),
        ("dash", "dash"),
        ("", ""),
    ],
)
def test_canonicalize_unit(surface: str, expect: str) -> None:
    assert canonicalize_unit(surface) == expect


@dataclass
class IngredientCase:
    input: str
    quantity: float
    unit: str
    food: str
    comments: str


@mark.parametrize(
    "testcase",
    [
        IngredientCase("1 tsp sugar", 1.0, "teaspoon", "sugar", ""),
        IngredientCase("0.5 teaspoons salt", 0.5, "teaspoon", "salt", ""),
        IngredientCase("2 1/4 cups almond flour", 2.25, "cup", "almond flour", ""),
        IngredientCase("½ cup all-purpose flour", 0.5, "cup", "all-purpose flour", ""),
        IngredientCase("1 ½ teaspoons ground black pepper", 1.5, "teaspoon", "black pepper", "ground"),
        IngredientCase("⅔ cup unsweetened flaked coconut", 0.667, "cup", "unsweetened flaked coconut", ""),
        IngredientCase("⅓ cup panko bread crumbs", 0.333, "cup", "panko bread crumbs", ""),
        IngredientCase("1/8 cup all-purpose flour", 0.125, "cup", "all-purpose flour", ""),
        IngredientCase("3.5 cup all-purpose flour", 3.5, "cup", "all-purpose flour", ""),
        IngredientCase("1/32 cup all-purpose flour", 0.031, "cup", "all-purpose flour", ""),
        IngredientCase("1 C parmesan cheese", 1.0, "cup", "parmesan cheese", ""),
    ],
)
def test_nlp_parser(testcase: IngredientCase):
    models = list_to_parsed_ingredients([testcase.input], Context())

    # Iterate over models and test_ingredients to gather
    for model, test_ingredient in zip(models, [testcase], strict=True):
        assert round(model.qty, 3) == pytest.approx(test_ingredient.quantity)

        assert model.comment == test_ingredient.comments
        assert model.name == test_ingredient.food
        assert model.unit == test_ingredient.unit


@mark.parametrize(
    "input,qty,unit",
    [
        # v2 ranks a low-confidence "slice" count ahead of the explicit weight;
        # prefer the weight instead.
        ("10 ounces white American cheese slices (about 16)", 10.0, "ounce"),
        # deliberate counts stay as counts even when a weight is also present
        ("4 boneless skinless chicken breasts (5 to 7 ounces each)", 4.0, ""),
        ("1 28-oz. can whole peeled tomatoes", 1.0, "can"),
    ],
)
def test_prefers_weight_over_uncertain_count(input: str, qty: float, unit: str):
    model = list_to_parsed_ingredients([input], Context())[0]
    assert model.qty == pytest.approx(qty)
    assert model.unit == unit
