from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.household import Name

Quantity = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class ShopItemCreate(BaseModel):
    name: Name
    quantity: Quantity = "1"
    category: CategoryName | None = None


class ShopItemUpdate(BaseModel):
    name: Name | None = None
    quantity: Quantity | None = None
    category: CategoryName | None = None
    checked: bool | None = None


class ShopItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    name: str
    quantity: str
    category: str | None
    checked: bool
    added_by: int | None
    created_at: datetime
