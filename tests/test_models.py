from lib.models import Ingredient, Recipe, Week


def test_ingredient_key_strips_and_lowercases():
    ingredient = Ingredient(item="  Garlic ", unit="  Tbsp ")
    assert ingredient.key() == ("garlic", "tbsp")


def test_search_text_includes_protein_words_tags_body_and_ingredients():
    recipe = Recipe(
        id="thai-beef",
        title="Thai Basil Beef",
        protein="minced_beef",
        carb="rice",
        time_min=20,
        tags=["weeknight", "Spicy"],
        ingredients=[Ingredient(item="Thai basil")],
        body="Fry the mince.",
    )
    text = recipe.search_text()
    assert "thai-beef" in text
    assert "thai basil beef" in text
    assert "minced beef" in text
    assert "rice" in text
    assert "weeknight" in text
    assert "spicy" in text
    assert "fry the mince." in text
    assert "thai basil" in text


def test_recipe_ids_follow_weekday_order_and_skip_empty_days():
    week = Week(
        id="w",
        title="Week",
        kind="planned",
        days={
            "friday": "fish",
            "monday": "beef",
            "wednesday": "",
        },
    )
    assert week.recipe_ids() == ["beef", "fish"]
