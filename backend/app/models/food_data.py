from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


UUID_DEFAULT = text("gen_random_uuid()")
NOW = func.now()


class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)

    ingredient_links: Mapped[list["IngredientAllergen"]] = relationship(back_populates="allergen")


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        UniqueConstraint("canonical_name", "state", name="uq_ingredients_name_state"),
        CheckConstraint("state IN ('raw', 'cooked')", name="ck_ingredients_state"),
        Index("ix_ingredients_canonical_name", "canonical_name"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    default_unit: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=NOW, onupdate=NOW, nullable=False
    )

    allergen_links: Mapped[list["IngredientAllergen"]] = relationship(back_populates="ingredient")
    nutrition_records: Mapped[list["IngredientNutrition"]] = relationship(back_populates="ingredient")
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="ingredient")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)


class IngredientAllergen(Base):
    __tablename__ = "ingredient_allergens"
    __table_args__ = (Index("ix_ingredient_allergens_allergen_id", "allergen_id"),)

    ingredient_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True
    )
    allergen_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True
    )
    source_note: Mapped[str] = mapped_column(Text, nullable=False)

    ingredient: Mapped[Ingredient] = relationship(back_populates="allergen_links")
    allergen: Mapped[Allergen] = relationship(back_populates="ingredient_links")


class NutritionSource(Base):
    __tablename__ = "nutrition_sources"
    __table_args__ = (UniqueConstraint("publisher", "reference", name="uq_nutrition_sources_publisher_reference"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    publisher: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ingredient_nutrition: Mapped[list["IngredientNutrition"]] = relationship(back_populates="nutrition_source")
    recipe_nutrition: Mapped[list["RecipeNutrition"]] = relationship(back_populates="nutrition_source")


class IngredientNutrition(Base):
    __tablename__ = "ingredient_nutrition"
    __table_args__ = (
        CheckConstraint("serving_quantity > 0", name="ck_ingredient_nutrition_quantity"),
        CheckConstraint("calories_kcal IS NULL OR calories_kcal >= 0", name="ck_ingredient_nutrition_calories"),
        CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_ingredient_nutrition_protein"),
        CheckConstraint("carbohydrate_g IS NULL OR carbohydrate_g >= 0", name="ck_ingredient_nutrition_carbohydrate"),
        CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_ingredient_nutrition_fat"),
        Index("ix_ingredient_nutrition_ingredient_created", "ingredient_id", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    ingredient_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False
    )
    nutrition_source_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("nutrition_sources.id", ondelete="RESTRICT"), nullable=False
    )
    serving_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    serving_unit: Mapped[str] = mapped_column(Text, nullable=False)
    calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    carbohydrate_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)

    ingredient: Mapped[Ingredient] = relationship(back_populates="nutrition_records")
    nutrition_source: Mapped[NutritionSource] = relationship(back_populates="ingredient_nutrition")


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint(
            "food_preference IN ('vegetarian', 'egg', 'non_vegetarian')",
            name="ck_recipes_food_preference",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    cuisine: Mapped[str] = mapped_column(Text, nullable=False)
    food_preference: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    current_version_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=NOW, onupdate=NOW, nullable=False
    )

    versions: Mapped[list["RecipeVersion"]] = relationship(
        back_populates="recipe", foreign_keys="RecipeVersion.recipe_id"
    )
    current_version: Mapped["RecipeVersion | None"] = relationship(
        foreign_keys=[current_version_id], uselist=False
    )


class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint("recipe_id", "version_number", name="uq_recipe_versions_recipe_version"),
        CheckConstraint("preparation_minutes >= 0", name="ck_recipe_versions_prep_minutes"),
        CheckConstraint("cooking_minutes >= 0", name="ck_recipe_versions_cooking_minutes"),
        CheckConstraint("servings > 0", name="ck_recipe_versions_servings"),
        CheckConstraint(
            "skill_level IN ('beginner', 'intermediate', 'experienced')",
            name="ck_recipe_versions_skill_level",
        ),
        Index("ix_recipe_versions_recipe_published", "recipe_id", text("published_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), server_default=UUID_DEFAULT, primary_key=True)
    recipe_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preparation_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cooking_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    servings: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    skill_level: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recipe: Mapped[Recipe] = relationship(back_populates="versions", foreign_keys=[recipe_id])
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe_version")
    cooking_steps: Mapped[list["CookingStep"]] = relationship(back_populates="recipe_version")
    nutrition: Mapped["RecipeNutrition | None"] = relationship(back_populates="recipe_version", uselist=False)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_recipe_ingredients_quantity"),
        CheckConstraint("ingredient_state IN ('raw', 'cooked')", name="ck_recipe_ingredients_state"),
        CheckConstraint("display_order > 0", name="ck_recipe_ingredients_display_order"),
        Index("ix_recipe_ingredients_ingredient_id", "ingredient_id"),
    )

    recipe_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    ingredient_state: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, primary_key=True)

    recipe_version: Mapped[RecipeVersion] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship(back_populates="recipe_ingredients")


class CookingStep(Base):
    __tablename__ = "cooking_steps"
    __table_args__ = (
        CheckConstraint("step_number > 0", name="ck_cooking_steps_number"),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0",
            name="ck_cooking_steps_duration",
        ),
    )

    recipe_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="CASCADE"), primary_key=True
    )
    step_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    recipe_version: Mapped[RecipeVersion] = relationship(back_populates="cooking_steps")


class RecipeNutrition(Base):
    __tablename__ = "recipe_nutrition"
    __table_args__ = (
        CheckConstraint("serving_size > 0", name="ck_recipe_nutrition_serving_size"),
        CheckConstraint("calories_kcal IS NULL OR calories_kcal >= 0", name="ck_recipe_nutrition_calories"),
        CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_recipe_nutrition_protein"),
        CheckConstraint("carbohydrate_g IS NULL OR carbohydrate_g >= 0", name="ck_recipe_nutrition_carbohydrate"),
        CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_recipe_nutrition_fat"),
        Index("ix_recipe_nutrition_source_id", "nutrition_source_id"),
    )

    recipe_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="CASCADE"), primary_key=True
    )
    nutrition_source_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("nutrition_sources.id", ondelete="RESTRICT"), nullable=False
    )
    serving_size: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    serving_unit: Mapped[str] = mapped_column(Text, nullable=False)
    calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    carbohydrate_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    calculation_note: Mapped[str] = mapped_column(Text, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=NOW, nullable=False)

    recipe_version: Mapped[RecipeVersion] = relationship(back_populates="nutrition")
    nutrition_source: Mapped[NutritionSource] = relationship(back_populates="recipe_nutrition")
