from dataclasses import dataclass

import pytest
from pytest import mark

from pkg.schema.web import Context
from pkg.services.parser.nlp_parser import list_to_parsed_ingredients, normalize_ingredient


@mark.parametrize(
    "input,expect",
    [
        ("1 tbsp. olive oil", "1 tablespoon olive oil"),
        ("2 tsp salt", "2 teaspoon salt"),
        ("3 cups flour", "3.0 cup flour"),
        ("4 oz. chicken breast", "4.0 ounce chicken breast"),
        ("5 cloves garlic, minced", "5 cloves garlic, minced"),
        ("6 slices whole wheat bread", "6 slices whole wheat bread"),
        ("7 grams sugar", "7.0 gram sugar"),
        ("8 fl. oz. milk", "8.0 fluid ounce milk"),
        ("9 lbs. beef", "9.0 pound beef"),
        ("10 ml vanilla extract", "10.0 milliliter vanilla extract"),
        ("10 ml", "10.0 milliliter"),
        ("1/2 cup chopped onions", "0.5 cup chopped onions"),
        ("3 1/2 cups diced tomatoes", "3.5 cup diced tomatoes"),
        ("2-3 tablespoons soy sauce", "2 1/2 tablespoon soy sauce"),
        ("1-1/2 cups water", "1.5 cup water"),
        ("2-1/4 cups almond flour", "2.25 cup almond flour"),
        # a stray trailing "/" from quantulum3 must not be consumed (regression:
        # this used to be non-deterministic across hash seeds)
        ("30g / 2 tbsp ghee or unsalted butter", "30.0 gram / 2 tablespoon ghee or unsalted butter"),
        ("1 to 2 teaspoons cayenne pepper", "1 1/2 teaspoon cayenne pepper"),
        ("1 ½ teaspoons ground black pepper", "1 1/2 teaspoon ground black pepper"),
        ("1 C parmesan cheese", "1.0 cup parmesan cheese"),
        (
            "¾ tsp. Diamond Crystal or ½ tsp. Morton kosher salt, plus more",
            "3/4 teaspoon Diamond Crystal or 1/2 teaspoon Morton kosher salt, plus more",
        ),
    ],
)
def test_normalize_ingredeint(input: str, expect: str) -> None:
    assert normalize_ingredient(input) == expect


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
        IngredientCase("1 ½ teaspoons ground black pepper", 1.5, "teaspoon", "black pepper", "ground"),
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
