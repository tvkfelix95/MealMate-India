# MealMate India Recipe Import Format

Version: `1.0`

This document defines one JSON document for importing a recipe and its current
version. It mirrors the existing split tables: `recipes`, `recipe_versions`,
`ingredients`, `recipe_ingredients`, `cooking_steps`, `nutrition_sources` and
`recipe_nutrition`.

## Safety rules

- `data_status` must be `verified` before publication. `illustrative` data is
  for fixtures and development only.
- Nutrition values must be numeric, non-negative, or `null`. `null` means
  unknown and must never be replaced with zero.
- A verified nutrition object requires a complete `source` with publisher,
  reference and retrieval timestamp.
- Allergen information is derived from verified `ingredient_allergens` data;
  it is not an independent recipe-table claim.
- The backend validators must pass before `publication_status` can become
  `ready` or `published`.
- IDs must be UUID strings. Existing IDs should be supplied when importing
  into the approved catalogue; generated IDs are an importer concern.

## Top-level shape

| Field | Type | Required | Rules |
|---|---|---:|---|
| `format_version` | string | yes | Must be `1.0`. |
| `data_status` | enum | yes | `illustrative` or `verified`. |
| `recipe` | object | yes | Recipe identity and current version. |

### `recipe`

| Field | Type | Required | Database mapping / rules |
|---|---|---:|---|
| `id` | UUID string | yes | Maps to `recipes.id`. |
| `slug` | string | yes | Non-empty and unique. |
| `title` | string | yes | Non-empty. |
| `cuisine` | string | yes | MVP value is `south_indian`; future values are data, not code branches. |
| `food_preference` | enum | yes | `vegetarian`, `egg` or `non_vegetarian`. |
| `is_active` | boolean | yes | Maps to `recipes.is_active`. |
| `current_version_id` | UUID string | yes | Must equal `version.id`; the version must belong to this recipe. |
| `publication_status` | enum | yes | `draft`, `ready` or `published`; maps to active/published fields during import. |
| `version` | object | yes | One recipe version represented by this document. |
| `allergen_info` | object | yes | Derived display metadata; validate against ingredient mappings. |

### `recipe.version`

| Field | Type | Required | Database mapping / rules |
|---|---|---:|---|
| `id` | UUID string | yes | Maps to `recipe_versions.id`; must belong to `recipe.id`. |
| `version_number` | integer | yes | Positive and unique per recipe. |
| `description` | string | optional | Required for publication; non-empty when supplied. |
| `preparation_minutes` | integer | yes | `>= 0`. |
| `cooking_minutes` | integer | yes | `>= 0`. |
| `servings` | integer | yes | `> 0`. |
| `skill_level` | enum | yes | `beginner`, `intermediate` or `experienced`. |
| `published_at` | timestamp/null | optional | Required when published; otherwise `null`. |
| `ingredients` | array | yes | At least one item for publication. |
| `steps` | array | yes | At least one item for publication. |
| `nutrition` | object/null | yes | Required with provenance for publication. |

### `version.ingredients[]`

Each item combines the shared ingredient record with its recipe-specific join
record. The importer must upsert or reference the shared ingredient separately.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `ingredient_id` | UUID string | yes | Maps to `ingredients.id`. |
| `canonical_name` | string | yes | Must match the shared ingredient record. |
| `state` | enum | yes | `raw` or `cooked`; maps to `ingredients.state`. |
| `default_unit` | string | yes | Maps to `ingredients.default_unit`. |
| `quantity` | decimal string/number | yes | `> 0`; maps to `recipe_ingredients.quantity`. |
| `unit` | string | yes | Non-empty recipe display unit. |
| `ingredient_state` | enum | yes | Must exactly equal `state`. |
| `display_order` | integer | yes | Positive and unique within the version. |

### `version.steps[]`

Maps to `cooking_steps`.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `step_number` | integer | yes | Positive and ordered. |
| `instruction` | string | yes | Non-empty, beginner-friendly instruction. |
| `duration_minutes` | integer/null | optional | `null` when unknown; otherwise `>= 0`. |

### `version.nutrition`

Maps to one `recipe_nutrition` row for the exact `version.id`.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `recipe_version_id` | UUID string | yes | Must equal `version.id`. |
| `serving_size` | decimal string/number | yes | `> 0`. |
| `serving_unit` | string | yes | Non-empty serving context. |
| `calories_kcal` | decimal/null | yes | Non-negative or `null`. |
| `protein_g` | decimal/null | yes | Non-negative or `null`. |
| `carbohydrate_g` | decimal/null | yes | Non-negative or `null`. |
| `fat_g` | decimal/null | yes | Non-negative or `null`. |
| `calculation_note` | string | yes | Explains the calculation or why values are unavailable. |
| `calculated_at` | timestamp | yes | Timestamp for the recorded values. |
| `source` | object/null | yes | Required and verified before publication. |

### `nutrition.source`

Maps to `nutrition_sources`. `null` is allowed only for draft/illustrative
data; a publishable record must include all required fields.

| Field | Type | Required when source exists | Rules |
|---|---|---:|---|
| `id` | UUID string | yes | Maps to `nutrition_sources.id`. |
| `publisher` | string | yes | Non-empty documented publisher. |
| `reference` | string | yes | Non-empty source reference or URL. |
| `retrieved_at` | timestamp | yes | When the source was retrieved. |
| `notes` | string/null | no | Optional provenance notes. |

### `recipe.allergen_info`

This is derived metadata, not a new database table. Each `allergen_id` must
resolve through `ingredient_allergens` for the recipe’s ingredients, and the
mapping must have its required `source_note`. For an illustrative fixture,
set `data_status` to `illustrative` and do not treat the list as verified.

```json
{
  "derived_from_ingredient_mappings": true,
  "items": [
    {
      "allergen_id": "00000000-0000-0000-0000-000000000091",
      "name": "milk",
      "source_note": "Illustrative fixture mapping; not verified.",
      "data_status": "illustrative"
    }
  ]
}
```

## Publication validation

Before `ready` or `published`, the backend must verify that:

1. The version belongs to the recipe and is the selected current version.
2. Every ingredient relationship exists and `ingredient_state` matches the
   catalog ingredient’s `state`.
3. Ingredients, steps, quantities, units, description and timings are present
   and valid.
4. Nutrition references the same version, has a valid source, and preserves
   unknown nutrient values as `null`.
5. Allergen mappings are documented and derived from the ingredients.

## Example mapping

The fixture at
[`backend/tests/fixtures/sample_recipe.json`](../backend/tests/fixtures/sample_recipe.json)
is intentionally illustrative and remains a draft. Its nutrition values are
`null`, and its source/allergen metadata are explicitly unverified.
