from fastapi import APIRouter, FastAPI

from app.admin import setup_admin
from app.routers import auth, products

tags_metadata = [
    {"name": "auth", "description": "Inscription, connexion (JWT) et profil courant"},
    {"name": "products", "description": "Produits du frigo de l'utilisateur connecté"},
    {"name": "health", "description": "Vérification de l'état du service"},
]

app = FastAPI(
    title="Fridge",
    description="Suivi des produits du frigo pour éviter le gaspillage.\n\n"
    "Authentification : `POST /api/v1/auth/login`, puis bouton **Authorize** ci-dessus.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
setup_admin(app)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(products.router)
app.include_router(api)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
