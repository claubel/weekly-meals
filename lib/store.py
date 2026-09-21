from __future__ import annotations

import re
from pathlib import Path

import frontmatter
import yaml

from lib.models import WEEKDAYS, Ingredient, Recipe, Week

ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "recipes"
TEMPLATES_DIR = ROOT / "weeks" / "templates"
PLANNED_DIR = ROOT / "weeks" / "planned"
PANTRY_PATH = ROOT / "pantry.yaml"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "recipe"


def _parse_ingredient(raw: object) -> Ingredient:
    if isinstance(raw, str):
        return Ingredient(item=raw)
    data = dict(raw or {})
    qty = data.get("qty")
    if qty is not None:
        qty = float(qty)
    return Ingredient(
        item=str(data.get("item", "")).strip(),
        aisle=str(data.get("aisle", "other") or "other"),
        qty=qty,
        unit=str(data.get("unit", "") or ""),
    )


def _recipe_from_post(post: frontmatter.Post, path: Path) -> Recipe:
    meta = post.metadata
    ingredients = [_parse_ingredient(x) for x in (meta.get("ingredients") or [])]
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return Recipe(
        id=str(meta.get("id") or path.stem),
        title=str(meta.get("title") or path.stem),
        protein=str(meta.get("protein") or "chicken"),
        carb=str(meta.get("carb") or "other"),
        time_min=int(meta.get("time_min") or 30),
        servings=int(meta.get("servings") or 1),
        tags=list(tags),
        ingredients=ingredients,
        body=(post.content or "").strip() + "\n",
        path=str(path),
    )


def _week_from_post(post: frontmatter.Post, path: Path) -> Week:
    meta = post.metadata
    days = {}
    nested = meta.get("days") or {}
    for day in WEEKDAYS:
        days[day] = str(nested.get(day) or meta.get(day) or "")
    return Week(
        id=str(meta.get("id") or path.stem),
        title=str(meta.get("title") or path.stem),
        kind=str(meta.get("kind") or "template"),
        why=str(meta.get("why") or ""),
        cook_first=str(meta.get("cook_first") or ""),
        days=days,
        body=(post.content or "").strip() + "\n",
        path=str(path),
    )


def dump_recipe_markdown(recipe: Recipe) -> str:
    ingredients = [
        {
            "aisle": ing.aisle,
            "item": ing.item,
            **({"qty": ing.qty} if ing.qty is not None else {}),
            **({"unit": ing.unit} if ing.unit else {}),
        }
        for ing in recipe.ingredients
    ]
    meta = {
        "id": recipe.id,
        "title": recipe.title,
        "protein": recipe.protein,
        "carb": recipe.carb,
        "time_min": recipe.time_min,
        "servings": recipe.servings,
        "tags": recipe.tags,
        "ingredients": ingredients,
    }
    post = frontmatter.Post(recipe.body.rstrip() + "\n", **meta)
    return frontmatter.dumps(post, sort_keys=False)


def dump_week_markdown(week: Week) -> str:
    meta = {
        "id": week.id,
        "kind": week.kind,
        "title": week.title,
        "why": week.why,
        "cook_first": week.cook_first,
        **{day: week.days.get(day, "") for day in WEEKDAYS},
    }
    body = week.body.strip() or "Saved from the planner.\n"
    post = frontmatter.Post(body.rstrip() + "\n", **meta)
    return frontmatter.dumps(post, sort_keys=False)


class Store:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self.recipes_dir = self.root / "recipes"
        self.templates_dir = self.root / "weeks" / "templates"
        self.planned_dir = self.root / "weeks" / "planned"
        self.pantry_path = self.root / "pantry.yaml"
        self.planned_dir.mkdir(parents=True, exist_ok=True)

    def load_recipes(self) -> list[Recipe]:
        recipes = []
        for path in sorted(self.recipes_dir.glob("*.md")):
            recipes.append(_recipe_from_post(frontmatter.load(path), path))
        recipes.sort(key=lambda r: r.title.lower())
        return recipes

    def recipe_by_id(self) -> dict[str, Recipe]:
        return {r.id: r for r in self.load_recipes()}

    def load_weeks(self, kind: str | None = None) -> list[Week]:
        weeks: list[Week] = []
        dirs = []
        if kind in (None, "template"):
            dirs.append(self.templates_dir)
        if kind in (None, "planned"):
            dirs.append(self.planned_dir)
        for folder in dirs:
            if not folder.exists():
                continue
            for path in sorted(folder.glob("*.md")):
                weeks.append(_week_from_post(frontmatter.load(path), path))
        return weeks

    def pantry(self) -> set[str]:
        if not self.pantry_path.exists():
            return set()
        data = yaml.safe_load(self.pantry_path.read_text()) or {}
        items = data.get("items") or []
        return {str(x).strip().lower() for x in items}

    def save_recipe(self, recipe: Recipe) -> Path:
        path = Path(recipe.path) if recipe.path else self.recipes_dir / f"{recipe.id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_recipe_markdown(recipe), encoding="utf-8")
        recipe.path = str(path)
        return path

    def save_week(self, week: Week) -> Path:
        folder = self.templates_dir if week.kind == "template" else self.planned_dir
        folder.mkdir(parents=True, exist_ok=True)
        path = Path(week.path) if week.path else folder / f"{week.id}.md"
        path.write_text(dump_week_markdown(week), encoding="utf-8")
        week.path = str(path)
        return path
