import shutil
from dataclasses import dataclass

import pytest
from pytest import mark

from app.ingredient_parser.crfpp.pre_processor import normalize_ingredient
from app.ingredient_parser.crfpp.processor import convert_list_to_crf_model


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
        ("1 to 2 teaspoons cayenne pepper", "1 1/2 teaspoon cayenne pepper"),
        ("1 ½ teaspoons ground black pepper", "1 1/2 teaspoon ground black pepper"),
        ("¾ tsp. Diamond Crystal or ½ tsp. Morton kosher salt, plus more", "3/4 teaspoon Diamond Crystal (or 1/2 teaspoon Morton kosher salt), plus more"),
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


def crf_exists() -> bool:
    return shutil.which("crf_test") is not None

# TODO - add more robust test cases
test_ingredients = [
    IngredientCase("½ cup all-purpose flour", 0.5, "cup", "all-purpose flour", ""),
    IngredientCase("1 ½ teaspoons ground black pepper", 1.5, "teaspoon", "black pepper", "ground"),
    IngredientCase("⅔ cup unsweetened flaked coconut", 0.667, "cup", "coconut", "unsweetened flaked"),
    IngredientCase("⅓ cup panko bread crumbs", 0.333, "cup", "panko bread crumbs", ""),
    IngredientCase("1/8 cup all-purpose flour", 0.125, "cup", "all-purpose flour", ""),
    IngredientCase("3.5 cup all-purpose flour", 3.5, "cup", "all-purpose flour", ""),
    IngredientCase("1/32 cup all-purpose flour", 0.031, "cup", "all-purpose flour", ""),
]

@mark.skipif(not crf_exists(), reason="CRF++ not installed")
def test_nlp_parser():
    models = convert_list_to_crf_model([x.input for x in test_ingredients])

    # Iterate over models and test_ingredients to gather
    for model, test_ingredient in zip(models, test_ingredients):
        assert round(model.qty, 3) == pytest.approx(test_ingredient.quantity)

        assert model.comment == test_ingredient.comments
        assert model.name == test_ingredient.food
        assert model.unit == test_ingredient.unit
