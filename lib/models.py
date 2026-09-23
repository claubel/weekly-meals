from __future__ import annotations

from dataclasses import dataclass, field


PROTEINS = [
    "minced_beef",
    "chicken",
    "tuna",
    "sardines",
    "white_fish",
]

CARBS = ["rice", "noodles", "potato", "bread", "other"]

PROTEIN_LABELS = {
    "minced_beef": "Minced beef",
    "chicken": "Chicken",
    "tuna": "Tuna",
    "sardines": "Sardines",
    "white_fish": "White fish",
}

CARB_LABELS = {
    "rice": "Rice",
    "noodles": "Noodles",
    "potato": "Potato",
    "bread": "Bread",
    "other": "Other",
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
WEEKDAY_LABELS = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
}

AISLES = ["protein", "veg", "carb", "other"]


@dataclass
class Ingredient:
    item: str
    aisle: str = "other"
    qty: float | None = None
    unit: str = ""

    def key(self) -> tuple[str, str]:
        return (self.item.strip().lower(), self.unit.strip().lower())


@dataclass
class Recipe:
    id: str
    title: str
    protein: str
    carb: str
    time_min: int
    servings: int = 1
    tags: list[str] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    body: str = ""
    path: str | None = None

    def search_text(self) -> str:
        bits = [
            self.id,
            self.title,
            self.protein.replace("_", " "),
            self.carb,
            " ".join(self.tags),
            self.body,
        ]
        bits.extend(ing.item for ing in self.ingredients)
        return " ".join(bits).lower()


@dataclass
class Week:
    id: str
    title: str
    kind: str  # template | planned
    why: str = ""
    days: dict[str, str] = field(default_factory=dict)
    body: str = ""
    path: str | None = None

    def recipe_ids(self) -> list[str]:
        return [self.days[d] for d in WEEKDAYS if self.days.get(d)]
