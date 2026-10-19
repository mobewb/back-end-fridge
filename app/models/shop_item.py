from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[str] = mapped_column(String(50), default="1", server_default="1")
    # Nom d'une catégorie (pas de FK : les catégories peuvent être supprimées/renommées).
    category: Mapped[str | None] = mapped_column(String(100))
    checked: Mapped[bool] = mapped_column(default=False, server_default="false")
    added_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
