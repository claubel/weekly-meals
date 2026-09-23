from lib.models import WEEKDAYS, Ingredient, Recipe, Week
from lib.store import Store, slugify


def test_slugify_normalizes_punctuation_and_blank_text():
    assert slugify("  Hello World! ") == "hello-world"
    assert slugify("Fish Meunière") == "fish-meuni-re"
    assert slugify("") == "recipe"
    assert slugify("---") == "recipe"


def _recipe() -> Recipe:
    return Recipe(
        id="lemon-chicken",
        title="Lemon Chicken",
        protein="chicken",
        carb="rice",
        time_min=25,
        servings=2,
        tags=["weeknight", "pan"],
        ingredients=[
            Ingredient(item="chicken thigh", aisle="protein", qty=2, unit="piece"),
            Ingredient(item="salt", aisle="other"),
        ],
        body="## Method\n\n1. Cook.\n",
    )


def test_save_and_load_recipe_round_trip(tmp_path):
    store = Store(tmp_path)
    path = store.save_recipe(_recipe())
    assert path == tmp_path / "recipes" / "lemon-chicken.md"

    loaded = store.load_recipes()
    assert len(loaded) == 1
    recipe = loaded[0]
    assert recipe.id == "lemon-chicken"
    assert recipe.title == "Lemon Chicken"
    assert recipe.protein == "chicken"
    assert recipe.carb == "rice"
    assert recipe.time_min == 25
    assert recipe.servings == 2
    assert recipe.tags == ["weeknight", "pan"]
    assert recipe.ingredients[0] == Ingredient(item="chicken thigh", aisle="protein", qty=2.0, unit="piece")
    assert recipe.ingredients[1] == Ingredient(item="salt", aisle="other", qty=None, unit="")
    assert "Cook." in recipe.body
    assert recipe.path == str(path)

    text = path.read_text(encoding="utf-8")
    salt_block = text.split("- aisle: other", 1)[1]
    assert "qty:" not in salt_block
    assert "unit:" not in salt_block


def test_load_recipes_sorts_by_title_and_parses_loose_frontmatter(tmp_path):
    recipes = tmp_path / "recipes"
    recipes.mkdir()
    (recipes / "z-first.md").write_text(
        """---
title: banana bowl
tags: tin, weeknight
ingredients:
  - lemon
  - aisle: veg
    item: spinach
    qty: 1
    unit: handful
---

Steam the spinach.
""",
        encoding="utf-8",
    )
    (recipes / "a-second.md").write_text(
        """---
title: Apple plate
---

Slice.
""",
        encoding="utf-8",
    )
    store = Store(tmp_path)
    loaded = store.load_recipes()
    assert [recipe.title for recipe in loaded] == ["Apple plate", "banana bowl"]

    loose = loaded[1]
    assert loose.id == "z-first"
    assert loose.protein == "chicken"
    assert loose.carb == "other"
    assert loose.time_min == 30
    assert loose.servings == 1
    assert loose.tags == ["tin", "weeknight"]
    assert loose.ingredients[0] == Ingredient(item="lemon")
    assert loose.ingredients[1].item == "spinach"
    assert loose.ingredients[1].qty == 1.0
    assert store.recipe_by_id()["a-second"].title == "Apple plate"


def test_save_recipe_keeps_an_existing_path(tmp_path):
    custom = tmp_path / "custom" / "dish.md"
    recipe = _recipe()
    recipe.path = str(custom)
    store = Store(tmp_path)
    assert store.save_recipe(recipe) == custom
    assert custom.is_file()


def test_save_week_uses_template_or_planned_folder(tmp_path):
    store = Store(tmp_path)
    template = Week(
        id="noodle-week",
        title="Noodle week",
        kind="template",
        why="One noodle bag.",
        cook_first="Soup first.",
        days={"monday": "soup", "friday": "sardines"},
        body="Notes.\n",
    )
    planned = Week(
        id="2026-09-23",
        title="This week",
        kind="planned",
        why="",
        cook_first="",
        days={day: "" for day in WEEKDAYS},
    )
    template_path = store.save_week(template)
    planned_path = store.save_week(planned)
    assert template_path == tmp_path / "weeks" / "templates" / "noodle-week.md"
    assert planned_path == tmp_path / "weeks" / "planned" / "2026-09-23.md"

    loaded_template = store.load_weeks("template")
    assert len(loaded_template) == 1
    assert loaded_template[0].days["monday"] == "soup"
    assert loaded_template[0].days["tuesday"] == ""
    assert loaded_template[0].why == "One noodle bag."
    assert "Notes." in loaded_template[0].body

    assert [week.id for week in store.load_weeks("planned")] == ["2026-09-23"]
    assert {week.id for week in store.load_weeks()} == {"noodle-week", "2026-09-23"}


def test_load_week_prefers_nested_days_and_defaults_missing_meta(tmp_path):
    templates = tmp_path / "weeks" / "templates"
    templates.mkdir(parents=True)
    (templates / "nested.md").write_text(
        """---
title: Nested days
days:
  friday: fish
  monday: beef
monday: ignored
---
""",
        encoding="utf-8",
    )
    store = Store(tmp_path)
    week = store.load_weeks("template")[0]
    assert week.id == "nested"
    assert week.kind == "template"
    assert week.title == "Nested days"
    assert week.days["monday"] == "beef"
    assert week.days["friday"] == "fish"
    assert week.days["tuesday"] == ""


def test_pantry_is_empty_when_missing_and_normalized_when_present(tmp_path):
    store = Store(tmp_path)
    assert store.pantry() == set()
    (tmp_path / "pantry.yaml").write_text(
        "items:\n  - Olive Oil\n  -  Salt \n",
        encoding="utf-8",
    )
    assert store.pantry() == {"olive oil", "salt"}
