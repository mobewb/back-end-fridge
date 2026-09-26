from sqlalchemy import update

from app.models import User

ADMIN = "http://test/admin"


async def _make_admin(client, engine, email: str, password: str = "motdepasse123") -> None:
    await client.post("/auth/register", json={"email": email, "password": password})
    # Passe par la même connexion transactionnelle que l'API (annulée en fin de test).
    from app.admin import SessionLocal

    async with SessionLocal() as db:
        await db.execute(update(User).where(User.email == email).values(is_admin=True))
        await db.commit()


async def test_admin_requires_login(client):
    r = await client.get(f"{ADMIN}/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].endswith("/admin/login")


async def test_admin_login_and_access(client, engine):
    await _make_admin(client, engine, "root@example.com")
    r = await client.post(
        f"{ADMIN}/login",
        data={"username": "root@example.com", "password": "motdepasse123"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert (await client.get(f"{ADMIN}/user/list")).status_code == 200
    assert (await client.get(f"{ADMIN}/product/list")).status_code == 200


async def test_non_admin_cannot_login(client):
    await client.post(
        "/auth/register", json={"email": "user@example.com", "password": "motdepasse123"}
    )
    r = await client.post(
        f"{ADMIN}/login",
        data={"username": "user@example.com", "password": "motdepasse123"},
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert (await client.get(f"{ADMIN}/user/list", follow_redirects=False)).status_code == 302


async def test_admin_wrong_password(client, engine):
    await _make_admin(client, engine, "root@example.com")
    r = await client.post(
        f"{ADMIN}/login",
        data={"username": "root@example.com", "password": "mauvais"},
        follow_redirects=False,
    )
    assert r.status_code == 400
