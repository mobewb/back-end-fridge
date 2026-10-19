from sqlalchemy import func, select

from app.models import Household, ShopItem


async def _create(client, h, name="Maison"):
    return await client.post("/household", json={"name": name}, headers=h)


async def test_no_household_404(client, auth_headers):
    h = await auth_headers()
    assert (await client.get("/household", headers=h)).status_code == 404
    assert (await client.post("/household/leave", headers=h)).status_code == 404


async def test_create_and_get(client, auth_headers):
    h = await auth_headers()
    r = await _create(client, h, "  Maison  ")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Maison"
    assert len(body["invite_code"]) == 8
    assert [m["email"] for m in body["members"]] == ["alice@example.com"]
    assert (await client.get("/household", headers=h)).json() == body


async def test_create_validation_and_conflict(client, auth_headers):
    h = await auth_headers()
    assert (await _create(client, h, "   ")).status_code == 422
    assert (await _create(client, h, "x" * 101)).status_code == 422
    assert (await _create(client, h)).status_code == 201
    assert (await _create(client, h)).status_code == 409


async def test_join(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    code = (await _create(client, alice)).json()["invite_code"]

    r = await client.post("/household/join", json={"invite_code": code}, headers=bob)
    assert r.status_code == 200
    assert {m["email"] for m in r.json()["members"]} == {"alice@example.com", "bob@example.com"}
    assert (
        await client.post("/household/join", json={"invite_code": code}, headers=bob)
    ).status_code == 409


async def test_join_bad_code_404(client, auth_headers):
    h = await auth_headers()
    r = await client.post("/household/join", json={"invite_code": "zzzzzzzz"}, headers=h)
    assert r.status_code == 404


async def test_leave_keeps_household_until_last_member(client, auth_headers, engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    created = (await _create(client, alice)).json()
    await client.post("/household/join", json={"invite_code": created["invite_code"]}, headers=bob)
    await client.post("/shop-items", json={"name": "Lait"}, headers=alice)

    assert (await client.post("/household/leave", headers=alice)).status_code == 204
    assert (await client.get("/household", headers=alice)).status_code == 404
    assert len((await client.get("/shop-items", headers=bob)).json()) == 1

    assert (await client.post("/household/leave", headers=bob)).status_code == 204
    # Le foyer et ses articles ont disparu.
    r = await client.post(
        "/household/join", json={"invite_code": created["invite_code"]}, headers=alice
    )
    assert r.status_code == 404
    async with AsyncSession(engine) as s:
        assert await s.scalar(select(func.count()).select_from(ShopItem)) == 0
        assert await s.get(Household, created["id"]) is None
