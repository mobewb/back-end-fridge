from datetime import date, timedelta


def _product(name: str, days: int, **extra) -> dict:
    return {"name": name, "expiry_date": (date.today() + timedelta(days=days)).isoformat(), **extra}


async def test_create_and_get(client, auth_headers):
    h = await auth_headers()
    r = await client.post("/products", json=_product("Lait", 1, quantity=2, unit="L"), headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["days_left"] == 1
    assert body["expired"] is False
    assert body["consumed"] is False
    r = await client.get(f"/products/{body['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "Lait"


async def test_create_rejects_invalid_quantity(client, auth_headers):
    h = await auth_headers()
    r = await client.post("/products", json=_product("Lait", 1, quantity=0), headers=h)
    assert r.status_code == 422


async def test_update_and_delete(client, auth_headers):
    h = await auth_headers()
    pid = (await client.post("/products", json=_product("Yaourt", 5), headers=h)).json()["id"]
    r = await client.patch(f"/products/{pid}", json={"consumed": True, "notes": "fini"}, headers=h)
    assert r.status_code == 200
    assert r.json()["consumed"] is True
    assert r.json()["notes"] == "fini"
    assert (await client.delete(f"/products/{pid}", headers=h)).status_code == 204
    assert (await client.get(f"/products/{pid}", headers=h)).status_code == 404


async def test_expiring_sorted_and_filtered(client, auth_headers):
    h = await auth_headers()
    for name, days in [("Lointain", 30), ("Demain", 1), ("Périmé", -2), ("Dans 3j", 3)]:
        await client.post("/products", json=_product(name, days), headers=h)
    consumed = (await client.post("/products", json=_product("Mangé", 0), headers=h)).json()["id"]
    await client.patch(f"/products/{consumed}", json={"consumed": True}, headers=h)

    r = await client.get("/products/expiring", params={"days": 3}, headers=h)
    assert r.status_code == 200
    assert [p["name"] for p in r.json()] == ["Périmé", "Demain", "Dans 3j"]
    assert r.json()[0]["expired"] is True
    assert r.json()[0]["days_left"] == -2


async def test_isolation_between_users(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    pid = (await client.post("/products", json=_product("Beurre", 4), headers=alice)).json()["id"]

    assert (await client.get(f"/products/{pid}", headers=bob)).status_code == 404
    assert (
        await client.patch(f"/products/{pid}", json={"name": "x"}, headers=bob)
    ).status_code == 404
    assert (await client.delete(f"/products/{pid}", headers=bob)).status_code == 404
    assert (await client.get("/products", headers=bob)).json() == []
    assert len((await client.get("/products", headers=alice)).json()) == 1
