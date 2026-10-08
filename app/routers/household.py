from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.models import Household, Membership, User
from app.schemas.household import HouseholdCreate, HouseholdJoin, HouseholdRead, MemberRead

router = APIRouter(prefix="/household", tags=["household"])

ALREADY_IN = "Vous appartenez déjà à un foyer"


async def _get_membership(db: DbSession, user: User) -> Membership | None:
    return await db.get(Membership, user.id)


async def _read(db: DbSession, household: Household) -> HouseholdRead:
    members = (
        await db.execute(
            select(User.id, User.email)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.household_id == household.id)
            .order_by(User.id)
        )
    ).all()
    return HouseholdRead(
        id=household.id,
        name=household.name,
        invite_code=household.invite_code,
        members=[MemberRead(id=m.id, email=m.email) for m in members],
    )


async def _commit_or_conflict(db: DbSession) -> None:
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_IN) from None


@router.get("", response_model=HouseholdRead)
async def get_household(db: DbSession, user: CurrentUser) -> HouseholdRead:
    membership = await _get_membership(db, user)
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun foyer")
    return await _read(db, await db.get_one(Household, membership.household_id))


@router.post("", response_model=HouseholdRead, status_code=status.HTTP_201_CREATED)
async def create_household(
    payload: HouseholdCreate, db: DbSession, user: CurrentUser
) -> HouseholdRead:
    if await _get_membership(db, user) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_IN)
    household = Household(name=payload.name)
    db.add(household)
    await db.flush()
    db.add(Membership(user_id=user.id, household_id=household.id))
    await _commit_or_conflict(db)
    return await _read(db, household)


@router.post("/join", response_model=HouseholdRead)
async def join_household(payload: HouseholdJoin, db: DbSession, user: CurrentUser) -> HouseholdRead:
    if await _get_membership(db, user) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_IN)
    household = await db.scalar(
        select(Household).where(Household.invite_code == payload.invite_code)
    )
    if household is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Code d'invitation invalide")
    db.add(Membership(user_id=user.id, household_id=household.id))
    await _commit_or_conflict(db)
    return await _read(db, household)


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_household(db: DbSession, user: CurrentUser) -> Response:
    membership = await _get_membership(db, user)
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun foyer")
    household_id = membership.household_id
    await db.delete(membership)
    await db.flush()
    remaining = await db.scalar(
        select(Membership.user_id).where(Membership.household_id == household_id).limit(1)
    )
    if remaining is None:
        # Les articles et adhésions sont supprimés par ON DELETE CASCADE.
        await db.execute(delete(Household).where(Household.id == household_id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
