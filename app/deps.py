from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Membership, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    user_id = decode_access_token(token)
    user = await db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_household_id(household_id: int, user: CurrentUser, db: DbSession) -> int:
    """Valide que l'utilisateur courant appartient au foyer du chemin."""
    if await db.get(Membership, (user.id, household_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foyer introuvable")
    return household_id


HouseholdId = Annotated[int, Depends(get_household_id)]
