from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("default_expiry_days > 0", name="ck_categories_expiry_positive"),
        # Unicité insensible à la casse par utilisateur (au niveau DB pour éviter les races
        # entre deux créations concurrentes du même nom).
        Index(
            "uq_categories_user_name_lower",
            "user_id",
            text("lower(name)"),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL = catégorie prédéfinie partagée par tous les utilisateurs ; sinon catégorie
    # personnalisée appartenant à user_id.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    emoji: Mapped[str] = mapped_column(String(8))
    default_expiry_days: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
