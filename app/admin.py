from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.config import settings
from app.db import SessionLocal, engine
from app.models import Category, Product, User
from app.security import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = str(form.get("username", "")).lower(), str(form.get("password", ""))
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_admin or not verify_password(password, user.hashed_password):
            return False
        request.session["admin_user_id"] = user.id
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if user_id is None:
            return False
        # Revalide à chaque requête : un admin rétrogradé ou supprimé perd l'accès immédiatement.
        async with SessionLocal() as db:
            user = await db.get(User, user_id)
        return user is not None and user.is_admin


class UserAdmin(ModelView, model=User):
    name = "Utilisateur"
    name_plural = "Utilisateurs"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.email, User.is_admin, User.created_at]
    column_searchable_list = [User.email]
    column_sortable_list = [User.id, User.email, User.created_at]
    column_default_sort = [(User.id, True)]
    # Le mot de passe n'est jamais affiché ni modifiable ici ; les comptes se créent via l'API.
    form_columns = [User.email, User.is_admin]
    can_create = False


class ProductAdmin(ModelView, model=Product):
    name = "Produit"
    name_plural = "Produits"
    icon = "fa-solid fa-carrot"
    column_list = [
        Product.id,
        Product.user_id,
        Product.name,
        Product.quantity,
        Product.category,
        Product.expiry_date,
        Product.consumed,
    ]
    column_searchable_list = [Product.name, Product.category]
    column_sortable_list = [Product.id, Product.name, Product.expiry_date, Product.consumed]
    column_default_sort = [(Product.expiry_date, False)]
    form_excluded_columns = [Product.created_at, Product.updated_at]


class CategoryAdmin(ModelView, model=Category):
    name = "Catégorie"
    name_plural = "Catégories"
    icon = "fa-solid fa-tags"
    column_list = [
        Category.id,
        Category.user_id,
        Category.name,
        Category.emoji,
        Category.default_expiry_days,
    ]
    column_searchable_list = [Category.name]
    column_sortable_list = [Category.id, Category.name, Category.default_expiry_days]
    column_default_sort = [(Category.name, False)]
    form_excluded_columns = [Category.created_at]


def setup_admin(app: FastAPI) -> Admin:
    admin = Admin(
        app,
        engine,
        title="Fridge admin",
        authentication_backend=AdminAuth(secret_key=settings.secret_key),
    )
    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(CategoryAdmin)
    return admin
