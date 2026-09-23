import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

FIXTURES = Path(__file__).parent / "fixtures"
APP = Path(__file__).parent.parent / "app.py"


@pytest.fixture
def meals_root(tmp_path, monkeypatch):
    root = tmp_path / "meals"
    shutil.copytree(FIXTURES, root)
    monkeypatch.setenv("WEEKLY_MEALS_ROOT", str(root))
    return root


def _by_label(widgets, label):
    matches = [widget for widget in widgets if widget.label == label]
    assert len(matches) == 1, f"expected one {label!r}, found {len(matches)}"
    return matches[0]


def _by_key(widgets, key):
    matches = [widget for widget in widgets if widget.key == key]
    assert len(matches) == 1, f"expected one widget {key!r}, found {len(matches)}"
    return matches[0]


def _open(meals_root):
    del meals_root
    return AppTest.from_file(str(APP)).run()


def _goto(at, page):
    at.sidebar.radio[0].set_value(page)
    at.run()
    # Changing page calls st.rerun(), which stops the script before the new page renders.
    return at.run()


def test_recipes_page_lists_both_fixture_recipes(meals_root):
    at = _open(meals_root)
    assert at.title[0].value == "Recipes"
    assert at.caption[0].value == "2 of 2 recipes"
    titles = " ".join(markdown.value for markdown in at.markdown)
    assert "Chicken rice" in titles
    assert "Tuna noodles" in titles


def test_protein_filter_hides_other_recipes(meals_root):
    at = _open(meals_root)
    _by_label(at.selectbox, "Protein").set_value("chicken")
    at.run()
    assert at.caption[0].value == "1 of 2 recipes"
    titles = " ".join(markdown.value for markdown in at.markdown)
    assert "Chicken rice" in titles
    assert "Tuna noodles" not in titles


def test_open_button_shows_the_recipe(meals_root):
    at = _open(meals_root)
    _by_key(at.button, "open-chicken-rice").click()
    at.run()
    at.run()
    assert at.title[0].value == "Chicken rice"
    body = " ".join(markdown.value for markdown in at.markdown)
    assert "Cook the rice" in body


def test_planner_builds_a_shopping_list_without_pantry_staples(meals_root):
    at = _goto(_open(meals_root), "Plan a week")
    assert any("Pick at least one dinner" in caption.value for caption in at.caption)

    _by_key(at.selectbox, "day-monday").set_value("chicken-rice")
    at.run()
    assert at.subheader[0].value == "Shopping list"
    items = set(at.dataframe[0].value["Item"])
    assert items == {"chicken thigh", "rice"}
    assert "salt" not in items


def test_saving_a_planned_week_writes_under_the_temp_root(meals_root):
    at = _goto(_open(meals_root), "Plan a week")
    _by_key(at.selectbox, "day-monday").set_value("chicken-rice")
    at.run()
    _by_label(at.text_input, "Save as id").set_value("Test Week")
    at.run()
    _by_label(at.button, "Save planned week").click()
    at.run()

    saved = meals_root / "weeks" / "planned" / "test-week.md"
    assert saved.is_file()
    text = saved.read_text(encoding="utf-8")
    assert "kind: planned" in text
    assert "monday: chicken-rice" in text
    assert any(message.value.endswith(str(saved)) or str(saved) in message.value for message in at.success)
