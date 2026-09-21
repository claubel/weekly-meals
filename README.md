# Weekday meals

Local Streamlit app for browsing, searching, and editing weeknight dinners, then planning Mon–Fri around a once-a-week grocery run.

Recipes live as one Markdown file each in `recipes/` (50 seeded dinners with ingredients and steps). Week templates live in `weeks/templates/` as Markdown with YAML frontmatter. Weeks you save from the planner go in `weeks/planned/`.

## How to run

From this folder, with Python 3.11+ (3.10 is fine):

```bash
cd meals
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The terminal prints a local URL (usually `http://localhost:8501`). Open it in your browser.

On Windows, activate with `.venv\Scripts\activate` instead of `source`.

### Without a venv

```bash
cd meals
pip install -r requirements.txt
streamlit run app.py
```

## What you can do

- **Recipes** — search by name, ingredient, or method; filter by protein and carb; open a recipe for ingredients and steps.
- **Edit / new recipe** — forms write back to the Markdown file (or create a new one). You can also edit files in Cursor.
- **Plan a week** — load one of the 10 grocery-run templates, or start empty, assign Mon–Fri, scale servings, save.
- **Saved weeks** — reopen a plan and copy the merged shopping list (pantry staples in `pantry.yaml` are omitted).

## Data layout

```
meals/
  app.py
  requirements.txt
  pantry.yaml
  recipes/*.md
  weeks/templates/*.md
  weeks/planned/*.md
```

Each recipe uses YAML frontmatter (`id`, `title`, `protein`, `carb`, `time_min`, `servings`, `tags`, `ingredients`) and a Markdown body with **Method** and **Notes**.

Edit `pantry.yaml` to change which staples are left off the shopping list (soy, oil, salt, garlic, and so on).

## Dependencies

Listed in `requirements.txt`: Streamlit, PyYAML, python-frontmatter.
