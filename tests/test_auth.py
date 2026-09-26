async def test_register_login_me(client, auth_headers):
    headers = await auth_headers("alice@example.com")
    r = await client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


async def test_register_duplicate_email(client):
    body = {"email": "bob@example.com", "password": "motdepasse123"}
    assert (await client.post("/auth/register", json=body)).status_code == 201
    assert (await client.post("/auth/register", json=body)).status_code == 409


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register", json={"email": "c@example.com", "password": "motdepasse123"}
    )
    r = await client.post("/auth/login", data={"username": "c@example.com", "password": "mauvais"})
    assert r.status_code == 401


async def test_products_require_auth(client):
    assert (await client.get("/products")).status_code == 401
