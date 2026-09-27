from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.models import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


async def _get_owned(db: DbSession, user: CurrentUser, category_id: int) -> Category:
    category = await db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Catégorie introuvable")
    return category


async def _name_taken(
    db: DbSession, user: CurrentUser, name: str, exclude_id: int | None = None
) -> bool:
    query = select(Category.id).where(
        or_(Category.user_id.is_(None), Category.user_id == user.id),
        func.lower(Category.name) == name.lower(),
    )
    if exclude_id is not None:
        query = query.where(Category.id != exclude_id)
    return await db.scalar(query) is not None


@router.get("", response_model=list[CategoryRead])
async def list_categories(db: DbSession, user: CurrentUser) -> list[Category]:
    query = (
        select(Category)
        .where(or_(Category.user_id.is_(None), Category.user_id == user.id))
        .order_by(Category.user_id.is_(None).desc(), Category.name)
    )
    return list((await db.scalars(query)).all())


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: DbSession, user: CurrentUser) -> Category:
    if await _name_taken(db, user, payload.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette catégorie existe déjà")
    category = Category(user_id=user.id, **payload.model_dump())
    db.add(category)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette catégorie existe déjà") from None
    await db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int, payload: CategoryUpdate, db: DbSession, user: CurrentUser
) -> Category:
    category = await _get_owned(db, user, category_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and await _name_taken(db, user, data["name"], exclude_id=category.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette catégorie existe déjà")
    for field, value in data.items():
        setattr(category, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette catégorie existe déjà") from None
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: DbSession, user: CurrentUser) -> Response:
    category = await _get_owned(db, user, category_id)
    await db.delete(category)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
