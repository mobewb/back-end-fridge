"""Données de référence : catégories prédéfinies partagées par tous les utilisateurs."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category

DEFAULT_CATEGORIES = [
    {"name": "Produits laitiers", "emoji": "🥛", "default_expiry_days": 7},
    {"name": "Viande", "emoji": "🥩", "default_expiry_days": 3},
    {"name": "Poisson", "emoji": "🐟", "default_expiry_days": 2},
    {"name": "Légumes", "emoji": "🥦", "default_expiry_days": 7},
    {"name": "Fruits", "emoji": "🍎", "default_expiry_days": 7},
    {"name": "Boulangerie", "emoji": "🍞", "default_expiry_days": 4},
    {"name": "Conserves", "emoji": "🥫", "default_expiry_days": 365},
    {"name": "Surgelés", "emoji": "🧊", "default_expiry_days": 180},
    {"name": "Boissons", "emoji": "🥤", "default_expiry_days": 30},
    {"name": "Restes", "emoji": "🍱", "default_expiry_days": 3},
    {"name": "Autre", "emoji": "📦", "default_expiry_days": 7},
]


async def seed_default_categories(db: AsyncSession) -> None:
    existing = await db.scalar(select(Category.id).where(Category.user_id.is_(None)).limit(1))
    if existing is not None:
        return
    db.add_all(Category(user_id=None, **category) for category in DEFAULT_CATEGORIES)
    await db.commit()
