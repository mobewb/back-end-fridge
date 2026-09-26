from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


async def _get_owned(db: DbSession, user: CurrentUser, product_id: int) -> Product:
    product = await db.scalar(
        select(Product).where(Product.id == product_id, Product.user_id == user.id)
    )
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: DbSession, user: CurrentUser) -> Product:
    data = payload.model_dump(exclude_none=True)
    product = Product(user_id=user.id, **data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
async def list_products(
    db: DbSession,
    user: CurrentUser,
    consumed: bool | None = None,
    category: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Product]:
    query = select(Product).where(Product.user_id == user.id)
    if consumed is not None:
        query = query.where(Product.consumed == consumed)
    if category is not None:
        query = query.where(Product.category == category)
    query = query.order_by(Product.expiry_date, Product.id).limit(limit).offset(offset)
    return list((await db.scalars(query)).all())


@router.get("/expiring", response_model=list[ProductRead])
async def expiring_products(
    db: DbSession, user: CurrentUser, days: Annotated[int, Query(ge=0, le=365)] = 3
) -> list[Product]:
    limit_date = date.today() + timedelta(days=days)
    query = (
        select(Product)
        .where(
            Product.user_id == user.id,
            Product.consumed.is_(False),
            Product.expiry_date <= limit_date,
        )
        .order_by(Product.expiry_date, Product.id)
    )
    return list((await db.scalars(query)).all())


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: DbSession, user: CurrentUser) -> Product:
    return await _get_owned(db, user, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, payload: ProductUpdate, db: DbSession, user: CurrentUser
) -> Product:
    product = await _get_owned(db, user, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None and field in {
            "name",
            "quantity",
            "expiry_date",
            "purchase_date",
            "consumed",
        }:
            continue
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: DbSession, user: CurrentUser) -> Response:
    product = await _get_owned(db, user, product_id)
    await db.delete(product)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
