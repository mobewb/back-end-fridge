from typing import Annotated

from pydantic import BaseModel, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class HouseholdCreate(BaseModel):
    name: Name


class HouseholdJoin(BaseModel):
    invite_code: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8)
    ]


class MemberRead(BaseModel):
    id: int
    email: str


class HouseholdRead(BaseModel):
    id: int
    name: str
    invite_code: str
    members: list[MemberRead]
