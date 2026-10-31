from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.main import app
from app.models.preferences import (
    Allergen,
    Equipment,
    Ingredient,
    UserAllergen,
    UserDislikedIngredient,
    UserEquipment,
    UserPreferences,
)
from app.models.profile import Profile


USER_A = UUID("00000000-0000-0000-0000-000000000001")
USER_B = UUID("00000000-0000-0000-0000-000000000002")
ALLERGEN_ID = uuid4()
INGREDIENT_ID = uuid4()
EQUIPMENT_ID = uuid4()
client = TestClient(app)


class FakeQuery:
    def __init__(self, db: "FakePreferencesDB", model: type) -> None:
        self.db = db
        self.model = model
        self.user_id = None

    def filter_by(self, user_id: UUID):
        self.user_id = user_id
        return self

    def all(self):
        rows = self.db.relations.get(self.model, [])
        return [row for row in rows if row.user_id == self.user_id]

    def delete(self, synchronize_session: bool = False) -> int:
        rows = self.db.relations.get(self.model, [])
        remaining = [row for row in rows if row.user_id != self.user_id]
        deleted = len(rows) - len(remaining)
        self.db.relations[self.model] = remaining
        return deleted


class FakePreferencesDB:
    def __init__(self, user_id: UUID = USER_A) -> None:
        now = datetime.now(timezone.utc)
        self.profiles = {user_id: Profile(user_id=user_id, created_at=now, updated_at=now)}
        self.preferences: dict[UUID, UserPreferences] = {}
        self.shared = {
            Allergen: {ALLERGEN_ID: Allergen(id=ALLERGEN_ID, name="Peanut")},
            Ingredient: {INGREDIENT_ID: Ingredient(id=INGREDIENT_ID, canonical_name="Onion", state="raw", is_active=True)},
            Equipment: {EQUIPMENT_ID: Equipment(id=EQUIPMENT_ID, name="Pan", is_active=True)},
        }
        self.relations = {
            UserAllergen: [],
            UserDislikedIngredient: [],
            UserEquipment: [],
        }

    def get(self, model: type, key: UUID):
        if model is Profile:
            return self.profiles.get(key)
        if model is UserPreferences:
            return self.preferences.get(key)
        return self.shared.get(model, {}).get(key)

    def query(self, model: type) -> FakeQuery:
        return FakeQuery(self, model)

    def add(self, item) -> None:
        if isinstance(item, UserPreferences):
            self.preferences[item.user_id] = item
        elif type(item) in self.relations:
            self.relations[type(item)].append(item)

    def commit(self) -> None:
        return None

    def refresh(self, item) -> None:
        if isinstance(item, UserPreferences):
            now = datetime.now(timezone.utc)
            item.created_at = item.created_at or now
            item.updated_at = now

    def rollback(self) -> None:
        return None


def override_dependencies(db: FakePreferencesDB, user_id: UUID = USER_A) -> None:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=str(user_id))


def payload(**overrides):
    value = {
        "food_preference": "vegetarian",
        "daily_budget_inr": "150.00",
        "skill_level": "beginner",
        "available_minutes": 30,
        "preferred_cuisines": ["south_indian"],
        "allergies": [str(ALLERGEN_ID)],
        "disliked_ingredients": [str(INGREDIENT_ID)],
        "kitchen_equipment": [str(EQUIPMENT_ID)],
    }
    value.update(overrides)
    return value


def test_put_saves_preferences_and_related_restrictions() -> None:
    db = FakePreferencesDB()
    override_dependencies(db)
    try:
        response = client.put("/api/v1/preferences/me", json=payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["food_preference"] == "vegetarian"
    assert response.json()["daily_budget_inr"] == "150.00"
    assert response.json()["allergies"] == [str(ALLERGEN_ID)]
    assert response.json()["disliked_ingredients"] == [str(INGREDIENT_ID)]
    assert response.json()["kitchen_equipment"] == [str(EQUIPMENT_ID)]


def test_get_returns_saved_preferences() -> None:
    db = FakePreferencesDB()
    db.preferences[USER_A] = UserPreferences(
        user_id=USER_A,
        food_preference="egg",
        daily_budget_inr=Decimal("200.00"),
        skill_level="intermediate",
        available_minutes=45,
        preferred_cuisine="south_indian",
    )
    db.relations[UserAllergen] = [UserAllergen(user_id=USER_A, allergen_id=ALLERGEN_ID)]
    override_dependencies(db)
    try:
        response = client.get("/api/v1/preferences/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["food_preference"] == "egg"
    assert response.json()["allergies"] == [str(ALLERGEN_ID)]


def test_put_preserves_allergies_when_not_supplied() -> None:
    db = FakePreferencesDB()
    db.preferences[USER_A] = UserPreferences(
        user_id=USER_A,
        food_preference="vegetarian",
        daily_budget_inr=Decimal("100.00"),
        skill_level="beginner",
        available_minutes=30,
        preferred_cuisine="south_indian",
    )
    db.relations[UserAllergen] = [UserAllergen(user_id=USER_A, allergen_id=ALLERGEN_ID)]
    override_dependencies(db)
    try:
        response = client.put(
            "/api/v1/preferences/me",
            json=payload(allergies=None, daily_budget_inr="125.00"),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["allergies"] == [str(ALLERGEN_ID)]
    assert response.json()["daily_budget_inr"] == "125.00"


def test_duplicate_entries_are_rejected() -> None:
    db = FakePreferencesDB()
    override_dependencies(db)
    try:
        response = client.put("/api/v1/preferences/me", json=payload(allergies=[str(ALLERGEN_ID), str(ALLERGEN_ID)]))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_unknown_reference_is_rejected() -> None:
    db = FakePreferencesDB()
    override_dependencies(db)
    try:
        response = client.put("/api/v1/preferences/me", json=payload(allergies=[str(uuid4())]))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_cross_user_isolation_prevents_reading_another_profile_preferences() -> None:
    db = FakePreferencesDB(user_id=USER_B)
    db.preferences[USER_B] = UserPreferences(
        user_id=USER_B,
        food_preference="non_vegetarian",
        daily_budget_inr=Decimal("500.00"),
        skill_level="experienced",
        available_minutes=60,
        preferred_cuisine="south_indian",
    )
    override_dependencies(db, USER_A)
    try:
        response = client.get("/api/v1/preferences/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert USER_A not in db.preferences
