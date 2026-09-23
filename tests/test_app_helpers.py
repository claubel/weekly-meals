import random

import pytest

import app
from lib.models import WEEKDAYS, Ingredient, Recipe, Week


def test_fmt_qty_formats_missing_integer_and_fractional_amounts():
    assert app.fmt_qty(Ingredient(item="salt")) == ""
    assert app.fmt_qty(Ingredient(item="salt", unit="pinch")) == "pinch"
    assert app.fmt_qty(Ingredient(item="rice", qty=2, unit="g")) == "2 g"
    assert app.fmt_qty(Ingredient(item="rice", qty=2, unit="")) == "2"
    assert app.fmt_qty(Ingredient(item="oil", qty=1.5, unit="tbsp")) == "1.5 tbsp"


def test_ingredient_yaml_round_trip_omits_blank_qty_and_unit():
    ingredients = [
        Ingredient(item="rice", aisle="carb", qty=1.5, unit="cup"),
        Ingredient(item="salt", aisle="other"),
        Ingredient(item="parsley", aisle="veg", qty=1, unit=""),
    ]
    loaded = app.yaml_to_ingredients(app.ingredients_to_yaml(ingredients))
    assert loaded[0] == ingredients[0]
    assert loaded[1] == Ingredient(item="salt", aisle="other", qty=None, unit="")
    assert loaded[2].qty == 1
    assert loaded[2].unit == ""


def test_yaml_to_ingredients_accepts_plain_strings_and_empty_text():
    assert app.yaml_to_ingredients("- lemon\n") == [Ingredient(item="lemon")]
    assert app.yaml_to_ingredients("") == []
    assert app.yaml_to_ingredients("[]") == []


def test_yaml_to_ingredients_rejects_a_mapping():
    with pytest.raises(ValueError, match="Ingredients must be a YAML list"):
        app.yaml_to_ingredients("item: rice\n")


def test_week_from_widgets_marks_the_week_as_saved_from_the_planner():
    week = app.week_from_widgets("Title", "why", "cook", {"monday": "a"}, "planned", "id-1")
    assert week == Week(
        id="id-1",
        title="Title",
        kind="planned",
        why="why",
        cook_first="cook",
        days={"monday": "a"},
        body="Saved from the planner.\n",
    )


def test_blank_and_loaded_drafts_cover_every_weekday():
    blank = app.blank_week_draft()
    assert blank["title"] == "My week"
    assert blank["cook_first"] == "Fish → chicken → mince → tins"
    assert list(blank["days"]) == WEEKDAYS
    assert set(blank["days"].values()) == {""}

    week = Week(
        id="w",
        title="Noodle week",
        kind="template",
        why="One bag.",
        cook_first="Soup first.",
        days={"monday": "soup", "friday": "sardines"},
    )
    draft = app.draft_from_week(week)
    assert draft["title"] == "Noodle week"
    assert draft["why"] == "One bag."
    assert draft["days"]["monday"] == "soup"
    assert draft["days"]["friday"] == "sardines"
    assert draft["days"]["tuesday"] == ""


def test_shuffled_blank_draft_is_stable_for_a_seed_and_does_not_repeat(monkeypatch):
    ids = ["a", "b", "c", "d", "e", "f"]
    monkeypatch.setattr(app, "recipe_options", lambda: {"": "— none —", **{i: i for i in ids}})

    random.seed(1)
    first = app.shuffled_blank_draft()
    random.seed(1)
    second = app.shuffled_blank_draft()

    assert first == second
    chosen = list(first["days"].values())
    assert list(first["days"]) == WEEKDAYS
    assert len(set(chosen)) == 5
    assert set(chosen) <= set(ids)
    assert first["title"] == "My week"


def test_shuffled_blank_draft_leaves_later_days_empty_when_recipes_run_out(monkeypatch):
    monkeypatch.setattr(app, "recipe_options", lambda: {"": "— none —", "a": "A", "b": "B"})
    random.seed(2)
    days = list(app.shuffled_blank_draft()["days"].values())
    assert set(days[:2]) == {"a", "b"}
    assert days[2:] == ["", "", ""]
