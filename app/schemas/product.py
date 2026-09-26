from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: float = Field(default=1, gt=0)
    unit: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, max_length=100)
    expiry_date: date
    notes: str | None = None


class ProductCreate(ProductBase):
    purchase_date: date | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, max_length=100)
    purchase_date: date | None = None
    expiry_date: date | None = None
    consumed: bool | None = None
    notes: str | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_date: date
    consumed: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def days_left(self) -> int:
        return (self.expiry_date - date.today()).days

    @computed_field
    @property
    def expired(self) -> bool:
        return self.days_left < 0
