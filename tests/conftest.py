import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://fridge:fridge@localhost:5432/fridge_test"
)


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(engine, monkeypatch) -> AsyncIterator[AsyncClient]:
    # Chaque test tourne dans une transaction annulée à la fin.
    async with engine.connect() as conn:
        trans = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )

        async def override_get_db():
            async with session_maker() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        monkeypatch.setattr("app.admin.SessionLocal", session_maker)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test/api/v1"
        ) as c:
            yield c
        app.dependency_overrides.clear()
        await trans.rollback()


async def register_and_login(client: AsyncClient, email: str) -> dict[str, str]:
    password = "motdepasse123"
    r = await client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    r = await client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth_headers(client):
    async def _make(email: str = "alice@example.com") -> dict[str, str]:
        return await register_and_login(client, email)

    return _make
