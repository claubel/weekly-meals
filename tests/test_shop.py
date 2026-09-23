from lib.models import Ingredient, Recipe
from lib.shop import merge_shopping_list


def _recipe(recipe_id: str, ingredients: list[Ingredient], servings: int = 1) -> Recipe:
    return Recipe(
        id=recipe_id,
        title=recipe_id,
        protein="chicken",
        carb="rice",
        time_min=20,
        servings=servings,
        ingredients=ingredients,
    )


def test_sums_same_item_and_unit_and_keeps_different_units():
    recipes = [
        _recipe("a", [Ingredient(item="Rice", aisle="carb", qty=100, unit="g")]),
        _recipe("b", [Ingredient(item=" rice ", aisle="carb", qty=50, unit="g")]),
        _recipe("c", [Ingredient(item="rice", aisle="carb", qty=1, unit="bag")]),
    ]
    merged = merge_shopping_list(recipes, pantry=set())
    by_unit = {item.unit: item for item in merged}
    assert by_unit["g"].qty == 150
    assert by_unit["g"].item == "Rice"
    assert by_unit["bag"].qty == 1


def test_skips_pantry_items_case_insensitively():
    recipe = _recipe(
        "a",
        [
            Ingredient(item=" Salt ", aisle="other", qty=1, unit="pinch"),
            Ingredient(item="chicken", aisle="protein", qty=1, unit="piece"),
        ],
    )
    merged = merge_shopping_list([recipe], pantry={"salt"})
    assert [item.item for item in merged] == ["chicken"]


def test_scales_quantity_by_multiplier_over_servings():
    recipe = _recipe(
        "a",
        [Ingredient(item="chicken", aisle="protein", qty=200, unit="g")],
        servings=2,
    )
    merged = merge_shopping_list([recipe], pantry=set(), servings_multiplier=1)
    assert merged[0].qty == 100

    doubled = merge_shopping_list([recipe], pantry=set(), servings_multiplier=2)
    assert doubled[0].qty == 200


def test_rounds_scaled_quantity_to_two_decimals():
    recipe = _recipe(
        "a",
        [Ingredient(item="oil", aisle="other", qty=1, unit="tbsp")],
        servings=3,
    )
    merged = merge_shopping_list([recipe], pantry=set())
    assert merged[0].qty == 0.33


def test_sorts_by_aisle_then_name():
    recipe = _recipe(
        "a",
        [
            Ingredient(item="zucchini", aisle="veg", qty=1, unit="piece"),
            Ingredient(item="apple", aisle="other", qty=1, unit="piece"),
            Ingredient(item="beef", aisle="protein", qty=1, unit="piece"),
            Ingredient(item="rice", aisle="carb", qty=1, unit="cup"),
        ],
    )
    names = [item.item for item in merge_shopping_list([recipe], pantry=set())]
    assert names == ["beef", "zucchini", "rice", "apple"]


def test_unspecified_quantity_does_not_replace_a_numeric_one():
    recipes = [
        _recipe("a", [Ingredient(item="parsley", aisle="veg", qty=1, unit="handful")]),
        _recipe("b", [Ingredient(item="parsley", aisle="veg", qty=None, unit="handful")]),
    ]
    merged = merge_shopping_list(recipes, pantry=set())
    assert len(merged) == 1
    assert merged[0].qty == 1


def test_numeric_quantity_does_not_fill_an_earlier_blank_quantity():
    recipes = [
        _recipe("a", [Ingredient(item="parsley", aisle="veg", qty=None, unit="handful")]),
        _recipe("b", [Ingredient(item="parsley", aisle="veg", qty=2, unit="handful")]),
    ]
    merged = merge_shopping_list(recipes, pantry=set())
    assert len(merged) == 1
    assert merged[0].qty is None


def test_empty_recipe_list_returns_no_items():
    assert merge_shopping_list([], pantry={"salt"}) == []
