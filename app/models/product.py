from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_products_quantity_positive"),
        Index("ix_products_user_expiry", "user_id", "expiry_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[float] = mapped_column(default=1)
    unit: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))
    purchase_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    expiry_date: Mapped[date] = mapped_column(Date)
    consumed: Mapped[bool] = mapped_column(default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
