from __future__ import annotations

from datetime import date

import streamlit as st
import yaml

from lib.models import (
    CARB_LABELS,
    CARBS,
    PROTEIN_LABELS,
    PROTEINS,
    WEEKDAY_LABELS,
    WEEKDAYS,
    Ingredient,
    Recipe,
    Week,
)
from lib.shop import merge_shopping_list
from lib.store import Store, slugify

st.set_page_config(page_title="Weekday meals", layout="wide")
store = Store()


def fmt_qty(ing: Ingredient) -> str:
    if ing.qty is None:
        return ing.unit or ""
    qty = ing.qty
    if float(qty).is_integer():
        qty = int(qty)
    return f"{qty} {ing.unit}".strip()


def ingredients_to_yaml(ingredients: list[Ingredient]) -> str:
    payload = [
        {
            "aisle": i.aisle,
            "item": i.item,
            **({"qty": i.qty} if i.qty is not None else {}),
            **({"unit": i.unit} if i.unit else {}),
        }
        for i in ingredients
    ]
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def yaml_to_ingredients(text: str) -> list[Ingredient]:
    data = yaml.safe_load(text) or []
    if not isinstance(data, list):
        raise ValueError("Ingredients must be a YAML list")
    out = []
    for raw in data:
        if isinstance(raw, str):
            out.append(Ingredient(item=raw))
            continue
        qty = raw.get("qty")
        out.append(
            Ingredient(
                item=str(raw.get("item", "")).strip(),
                aisle=str(raw.get("aisle", "other") or "other"),
                qty=None if qty is None else float(qty),
                unit=str(raw.get("unit", "") or ""),
            )
        )
    return out


def shopping_rows(recipes: list[Recipe], multiplier: float) -> list[dict]:
    pantry = store.pantry()
    merged = merge_shopping_list(recipes, pantry, multiplier)
    return [
        {
            "Aisle": i.aisle,
            "Item": i.item,
            "Amount": fmt_qty(i),
        }
        for i in merged
    ]


def recipe_options() -> dict[str, str]:
    recipes = store.load_recipes()
    return {"": "— none —", **{r.id: f"{r.title} ({PROTEIN_LABELS.get(r.protein, r.protein)})" for r in recipes}}


def page_recipes() -> None:
    recipes = store.load_recipes()
    st.title("Recipes")
    col1, col2, col3 = st.columns(3)
    with col1:
        query = st.text_input("Search", placeholder="Name, veg, method…")
    with col2:
        protein = st.selectbox(
            "Protein",
            ["all", *PROTEINS],
            format_func=lambda x: "All" if x == "all" else PROTEIN_LABELS.get(x, x),
        )
    with col3:
        carb = st.selectbox(
            "Carb",
            ["all", *CARBS],
            format_func=lambda x: "All" if x == "all" else CARB_LABELS.get(x, x),
        )

    q = (query or "").strip().lower()
    filtered = []
    for recipe in recipes:
        if protein != "all" and recipe.protein != protein:
            continue
        if carb != "all" and recipe.carb != carb:
            continue
        if q and q not in recipe.search_text():
            continue
        filtered.append(recipe)

    st.caption(f"{len(filtered)} of {len(recipes)} recipes")
    for recipe in filtered:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{recipe.title}**")
                st.caption(
                    f"{PROTEIN_LABELS.get(recipe.protein, recipe.protein)} · "
                    f"{CARB_LABELS.get(recipe.carb, recipe.carb)} · {recipe.time_min} min"
                )
            with right:
                if st.button("Open", key=f"open-{recipe.id}"):
                    st.session_state["recipe_id"] = recipe.id
                    st.session_state["page"] = "Recipe"
                    st.rerun()


def recipe_form(recipe: Recipe, *, is_new: bool) -> None:
    with st.form("recipe-form"):
        title = st.text_input("Title", value=recipe.title)
        default_id = slugify(title) if is_new else recipe.id
        rid = st.text_input("Id (filename slug)", value=default_id, disabled=not is_new)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            protein = st.selectbox(
                "Protein",
                PROTEINS,
                index=PROTEINS.index(recipe.protein) if recipe.protein in PROTEINS else 0,
                format_func=lambda x: PROTEIN_LABELS[x],
            )
        with c2:
            carb = st.selectbox(
                "Carb",
                CARBS,
                index=CARBS.index(recipe.carb) if recipe.carb in CARBS else 0,
                format_func=lambda x: CARB_LABELS[x],
            )
        with c3:
            time_min = st.number_input("Time (min)", min_value=5, max_value=180, value=recipe.time_min)
        with c4:
            servings = st.number_input("Servings", min_value=1, max_value=8, value=recipe.servings)
        tags = st.text_input("Tags (comma-separated)", value=", ".join(recipe.tags))
        ingredients_text = st.text_area(
            "Ingredients (YAML list)",
            value=ingredients_to_yaml(recipe.ingredients),
            height=220,
        )
        body = st.text_area("Method and notes (Markdown)", value=recipe.body, height=280)
        submitted = st.form_submit_button("Save")

    if not submitted:
        return
    try:
        ingredients = yaml_to_ingredients(ingredients_text)
    except Exception as exc:
        st.error(f"Could not parse ingredients: {exc}")
        return
    saved = Recipe(
        id=slugify(rid) if is_new else recipe.id,
        title=title.strip() or recipe.title,
        protein=protein,
        carb=carb,
        time_min=int(time_min),
        servings=int(servings),
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        ingredients=ingredients,
        body=body,
        path=None if is_new else recipe.path,
    )
    path = store.save_recipe(saved)
    st.success(f"Saved {path.name}")
    st.session_state["recipe_id"] = saved.id
    st.session_state["page"] = "Recipe"
    st.rerun()


def page_recipe() -> None:
    recipes = store.recipe_by_id()
    ids = list(recipes)
    if not ids:
        st.info("No recipes yet.")
        return
    current = st.session_state.get("recipe_id") or ids[0]
    if current not in recipes:
        current = ids[0]
    recipe = recipes[current]
    st.title(recipe.title)
    picked = st.selectbox(
        "Recipe",
        ids,
        index=ids.index(recipe.id),
        format_func=lambda i: recipes[i].title,
    )
    if picked != recipe.id:
        st.session_state["recipe_id"] = picked
        st.rerun()

    st.caption(
        f"{PROTEIN_LABELS.get(recipe.protein, recipe.protein)} · "
        f"{CARB_LABELS.get(recipe.carb, recipe.carb)} · {recipe.time_min} min · "
        f"{recipe.servings} serving{'s' if recipe.servings != 1 else ''}"
    )
    if recipe.tags:
        st.write(" · ".join(recipe.tags))

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Ingredients")
        for ing in recipe.ingredients:
            st.write(f"{fmt_qty(ing)} {ing.item}".strip())
    with right:
        st.markdown(recipe.body)

    with st.expander("Edit this recipe"):
        recipe_form(recipe, is_new=False)


def page_new() -> None:
    st.title("New recipe")
    blank = Recipe(
        id="",
        title="",
        protein="chicken",
        carb="rice",
        time_min=25,
        servings=1,
        tags=["weeknight"],
        ingredients=[Ingredient(item="", aisle="protein", qty=1, unit="")],
        body="## Method\n\n1. \n\n## Notes\n\n",
    )
    recipe_form(blank, is_new=True)


def week_from_widgets(title: str, why: str, cook_first: str, days: dict[str, str], kind: str, week_id: str) -> Week:
    return Week(
        id=week_id,
        title=title,
        kind=kind,
        why=why,
        cook_first=cook_first,
        days=days,
        body="Saved from the planner.\n",
    )


def page_planner() -> None:
    st.title("Plan a week")
    templates = store.load_weeks("template")
    template_map = {t.id: t for t in templates}
    source = st.selectbox(
        "Start from",
        ["blank", *[t.id for t in templates]],
        format_func=lambda x: "Blank week" if x == "blank" else template_map[x].title,
    )
    if st.button("Load into planner"):
        if source == "blank":
            st.session_state["draft"] = {
                "title": "My week",
                "why": "",
                "cook_first": "Fish → chicken → mince → tins",
                "days": {d: "" for d in WEEKDAYS},
            }
        else:
            week = template_map[source]
            st.session_state["draft"] = {
                "title": week.title,
                "why": week.why,
                "cook_first": week.cook_first,
                "days": dict(week.days),
            }
        st.rerun()

    draft = st.session_state.get("draft") or {
        "title": "My week",
        "why": "",
        "cook_first": "Fish → chicken → mince → tins",
        "days": {d: "" for d in WEEKDAYS},
    }

    title = st.text_input("Week title", value=draft["title"])
    why = st.text_area("Why this grouping works", value=draft["why"], height=80)
    cook_first = st.text_input("Cook this first", value=draft["cook_first"])
    options = recipe_options()
    days: dict[str, str] = {}
    cols = st.columns(5)
    for i, day in enumerate(WEEKDAYS):
        with cols[i]:
            current = draft["days"].get(day, "")
            keys = list(options)
            index = keys.index(current) if current in options else 0
            days[day] = st.selectbox(WEEKDAY_LABELS[day], keys, index=index, format_func=lambda k: options[k], key=f"day-{day}")

    recipes_by_id = store.recipe_by_id()
    chosen = [recipes_by_id[rid] for rid in days.values() if rid in recipes_by_id]
    multiplier = st.number_input("Servings multiplier", min_value=0.5, max_value=4.0, value=1.0, step=0.5)
    if cook_first:
        st.info(cook_first)
    if why:
        st.write(why)

    if chosen:
        st.subheader("Shopping list")
        st.caption("Pantry staples from pantry.yaml are omitted. Quantities are for the meals above.")
        rows = shopping_rows(chosen, float(multiplier))
        st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button(
            "Download shopping list (CSV)",
            data="Aisle,Item,Amount\n" + "\n".join(f"{r['Aisle']},{r['Item']},{r['Amount']}" for r in rows),
            file_name="shopping-list.csv",
            mime="text/csv",
        )
    else:
        st.caption("Pick at least one dinner to build a shopping list.")

    save_id = st.text_input("Save as id", value=str(date.today()))
    if st.button("Save planned week", type="primary"):
        week = week_from_widgets(title, why, cook_first, days, "planned", slugify(save_id))
        path = store.save_week(week)
        st.success(f"Saved {path}")


def page_saved() -> None:
    st.title("Saved weeks")
    weeks = store.load_weeks("planned")
    if not weeks:
        st.info("No saved weeks yet. Plan a week and click Save.")
        return
    picked_id = st.selectbox("Week", [w.id for w in weeks], format_func=lambda i: next(w.title for w in weeks if w.id == i) + f" ({i})")
    week = next(w for w in weeks if w.id == picked_id)
    st.write(week.why)
    if week.cook_first:
        st.info(week.cook_first)
    recipes_by_id = store.recipe_by_id()
    for day in WEEKDAYS:
        rid = week.days.get(day, "")
        recipe = recipes_by_id.get(rid)
        label = recipe.title if recipe else (rid or "—")
        cols = st.columns([3, 1])
        cols[0].write(f"**{WEEKDAY_LABELS[day]}** — {label}")
        if recipe and cols[1].button("Open", key=f"saved-{day}"):
            st.session_state["recipe_id"] = recipe.id
            st.session_state["page"] = "Recipe"
            st.rerun()
    chosen = [recipes_by_id[rid] for rid in week.recipe_ids() if rid in recipes_by_id]
    multiplier = st.number_input("Servings multiplier", min_value=0.5, max_value=4.0, value=1.0, step=0.5, key="saved-mult")
    if chosen:
        rows = shopping_rows(chosen, float(multiplier))
        st.subheader("Shopping list")
        st.dataframe(rows, hide_index=True, width="stretch")


PAGES = {
    "Recipes": page_recipes,
    "Recipe": page_recipe,
    "New recipe": page_new,
    "Plan a week": page_planner,
    "Saved weeks": page_saved,
}


def main() -> None:
    if "page" not in st.session_state:
        st.session_state["page"] = "Recipes"
    page = st.sidebar.radio("Go to", list(PAGES), index=list(PAGES).index(st.session_state["page"]))
    if page != st.session_state["page"]:
        st.session_state["page"] = page
        st.rerun()
    PAGES[st.session_state["page"]]()


main()
