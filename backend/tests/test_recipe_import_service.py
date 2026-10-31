import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.food_data import (
    Allergen,
    Ingredient,
    IngredientAllergen,
    NutritionSource,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeVersion,
    CookingStep,
)
from app.schemas.recipe_import import RecipeImport
from app.services.recipe_import import RecipeImportConflictError, RecipeImportError, import_recipe


FIXTURE = Path(__file__).parent / "fixtures" / "sample_recipe.json"


class FakeQuery:
    def __init__(self, db: "FakeImportDB", model: type) -> None:
        self.db = db
        self.model = model
        self.filters: dict[str, object] = {}

    def filter_by(self, **filters: object) -> "FakeQuery":
        self.filters = filters
        return self

    def one_or_none(self):
        matches = [
            item
            for item in self.db.items(self.model)
            if all(getattr(item, key) == value for key, value in self.filters.items())
        ]
        if len(matches) > 1:
            raise AssertionError("fake query found more than one row")
        return matches[0] if matches else None


class FakeImportDB:
    def __init__(self) -> None:
        self.rows: dict[type, list[object]] = {}
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_on_flush = False

    def items(self, model: type) -> list[object]:
        return self.rows.get(model, [])

    def get(self, model: type, identifier):
        return next((row for row in self.items(model) if getattr(row, "id", None) == identifier), None)

    def query(self, model: type) -> FakeQuery:
        return FakeQuery(self, model)

    def add(self, item: object) -> None:
        self.rows.setdefault(type(item), []).append(item)

    def flush(self) -> None:
        if self.fail_on_flush:
            raise SQLAlchemyError("simulated failure")

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def load_sample() -> RecipeImport:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return RecipeImport.model_validate(payload)


def test_draft_import_creates_catalogue_rows_and_preserves_unknown_nutrition() -> None:
    db = FakeImportDB()

    recipe = import_recipe(db, load_sample())

    assert recipe.id == UUID("00000000-0000-0000-0000-000000000101")
    assert len(db.items(Recipe)) == 1
    assert len(db.items(RecipeVersion)) == 1
    assert len(db.items(Ingredient)) == 5
    assert len(db.items(RecipeIngredient)) == 5
    assert len(db.items(CookingStep)) == 3
    assert not db.items(RecipeNutrition)
    assert len(db.items(Allergen)) == 1
    assert db.commit_count == 1
    assert db.rollback_count == 0


def test_existing_recipe_identity_is_rejected_and_rolled_back() -> None:
    db = FakeImportDB()
    db.add(Recipe(id=UUID("00000000-0000-0000-0000-000000000101"), slug="existing"))

    with pytest.raises(RecipeImportConflictError, match="identifier already exists"):
        import_recipe(db, load_sample())

    assert db.commit_count == 0
    assert db.rollback_count == 1


def test_conflicting_shared_ingredient_is_rejected() -> None:
    db = FakeImportDB()
    db.add(
        Ingredient(
            id=UUID("00000000-0000-0000-0000-000000000111"),
            canonical_name="rice",
            state="cooked",
            default_unit="g",
            is_active=True,
        )
    )

    with pytest.raises(RecipeImportConflictError, match="conflicts"):
        import_recipe(db, load_sample())

    assert db.commit_count == 0
    assert db.rollback_count == 1


def test_nutrition_must_reference_imported_version() -> None:
    document = load_sample()
    assert document.recipe.version.nutrition is not None
    document.recipe.version.nutrition.recipe_version_id = uuid4()
    db = FakeImportDB()

    with pytest.raises(RecipeImportError, match="recipe version"):
        import_recipe(db, document)

    assert db.commit_count == 0
    assert db.rollback_count == 1


def test_database_failure_rolls_back_without_commit() -> None:
    db = FakeImportDB()
    db.fail_on_flush = True

    with pytest.raises(RecipeImportError, match="could not be saved"):
        import_recipe(db, load_sample())

    assert db.commit_count == 0
    assert db.rollback_count == 1
