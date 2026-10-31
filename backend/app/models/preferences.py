from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.food_data import Allergen, Equipment, Ingredient


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    food_preference: Mapped[str] = mapped_column(Text, nullable=False)
    daily_budget_inr: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    skill_level: Mapped[str] = mapped_column(Text, nullable=False)
    available_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    preferred_cuisine: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UserAllergen(Base):
    __tablename__ = "user_allergens"

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    allergen_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True
    )
    allergen: Mapped[Allergen] = relationship("Allergen")


class UserDislikedIngredient(Base):
    __tablename__ = "user_disliked_ingredients"

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient: Mapped[Ingredient] = relationship("Ingredient")


class UserEquipment(Base):
    __tablename__ = "user_equipment"

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    equipment_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True
    )
    equipment: Mapped[Equipment] = relationship("Equipment")


__all__ = [
    "Allergen",
    "Equipment",
    "Ingredient",
    "UserAllergen",
    "UserDislikedIngredient",
    "UserEquipment",
    "UserPreferences",
]
