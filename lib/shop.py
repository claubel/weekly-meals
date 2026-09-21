from __future__ import annotations

from collections import defaultdict

from lib.models import Ingredient, Recipe


def merge_shopping_list(
    recipes: list[Recipe],
    pantry: set[str],
    servings_multiplier: float = 1.0,
) -> list[Ingredient]:
    """Sum qty for the same item+unit, skip pantry staples, scale servings."""
    buckets: dict[tuple[str, str], Ingredient] = {}
    extra_notes: dict[tuple[str, str], list[str]] = defaultdict(list)

    for recipe in recipes:
        scale = servings_multiplier / max(recipe.servings or 1, 1)
        for ing in recipe.ingredients:
            if ing.item.strip().lower() in pantry:
                continue
            key = ing.key()
            existing = buckets.get(key)
            qty = None if ing.qty is None else round(ing.qty * scale, 2)
            if existing is None:
                buckets[key] = Ingredient(
                    item=ing.item.strip(),
                    aisle=ing.aisle or "other",
                    qty=qty,
                    unit=ing.unit,
                )
            elif qty is not None and existing.qty is not None:
                existing.qty = round(existing.qty + qty, 2)
            elif qty is not None and existing.qty is None:
                extra_notes[key].append(f"+ {qty} {ing.unit}".strip())
            elif qty is None:
                extra_notes[key].append("see recipe")

    aisle_order = {"protein": 0, "veg": 1, "carb": 2, "other": 3}
    items = list(buckets.values())
    items.sort(key=lambda i: (aisle_order.get(i.aisle, 9), i.item.lower()))
    return items
