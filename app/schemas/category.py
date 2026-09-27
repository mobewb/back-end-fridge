from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    emoji: str = Field(min_length=1, max_length=8)
    default_expiry_days: int = Field(gt=0, le=3650)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    emoji: str | None = Field(default=None, min_length=1, max_length=8)
    default_expiry_days: int | None = Field(default=None, gt=0, le=3650)


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    created_at: datetime

    @computed_field
    @property
    def is_default(self) -> bool:
        return self.user_id is None
