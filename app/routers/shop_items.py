from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, select

from app.deps import CurrentUser, DbSession, HouseholdId
from app.models import ShopItem
from app.schemas.shop_item import ShopItemCreate, ShopItemRead, ShopItemUpdate

router = APIRouter(prefix="/households/{household_id}/shop-items", tags=["shop-items"])


async def _get_owned(db: DbSession, household_id: int, item_id: int) -> ShopItem:
    item = await db.scalar(
        select(ShopItem).where(ShopItem.id == item_id, ShopItem.household_id == household_id)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article introuvable")
    return item


@router.get("", response_model=list[ShopItemRead])
async def list_shop_items(db: DbSession, household_id: HouseholdId) -> list[ShopItem]:
    query = (
        select(ShopItem)
        .where(ShopItem.household_id == household_id)
        .order_by(ShopItem.checked, ShopItem.created_at.desc(), ShopItem.id.desc())
    )
    return list((await db.scalars(query)).all())


@router.post("", response_model=ShopItemRead, status_code=status.HTTP_201_CREATED)
async def create_shop_item(
    payload: ShopItemCreate, db: DbSession, user: CurrentUser, household_id: HouseholdId
) -> ShopItem:
    item = ShopItem(household_id=household_id, added_by=user.id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ShopItemRead)
async def update_shop_item(
    item_id: int, payload: ShopItemUpdate, db: DbSession, household_id: HouseholdId
) -> ShopItem:
    item = await _get_owned(db, household_id, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        # name/quantity/checked sont non nullables : null explicite = invalide.
        if value is None and field != "category":
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"{field} ne peut pas être nul"
            )
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shop_item(item_id: int, db: DbSession, household_id: HouseholdId) -> Response:
    await db.delete(await _get_owned(db, household_id, item_id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_checked(
    db: DbSession, household_id: HouseholdId, checked: bool = False
) -> Response:
    if not checked:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Paramètre checked=true requis")
    await db.execute(
        delete(ShopItem).where(ShopItem.household_id == household_id, ShopItem.checked.is_(True))
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
