from fastapi import APIRouter, FastAPI

from app.admin import setup_admin
from app.routers import auth, products

app = FastAPI(title="Fridge", description="Suivi des produits du frigo")
setup_admin(app)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(products.router)
app.include_router(api)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
