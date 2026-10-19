from sqlalchemy import func, select

from app.models import Household, ShopItem


async def _create(client, h, name="Maison"):
    return await client.post("/households", json={"name": name}, headers=h)


async def test_no_household(client, auth_headers):
    h = await auth_headers()
    assert (await client.get("/households", headers=h)).json() == []
    assert (await client.get("/households/999999", headers=h)).status_code == 404
    assert (await client.post("/households/999999/leave", headers=h)).status_code == 404


async def test_create_and_get(client, auth_headers):
    h = await auth_headers()
    r = await _create(client, h, "  Maison  ")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Maison"
    assert len(body["invite_code"]) == 8
    assert [m["email"] for m in body["members"]] == ["alice@example.com"]
    assert (await client.get(f"/households/{body['id']}", headers=h)).json() == body
    assert (await client.get("/households", headers=h)).json() == [body]


async def test_create_validation(client, auth_headers):
    h = await auth_headers()
    assert (await _create(client, h, "   ")).status_code == 422
    assert (await _create(client, h, "x" * 101)).status_code == 422


async def test_multiple_households_per_user(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    first = (await _create(client, alice, "Maison")).json()
    second = (await _create(client, alice, "Vacances")).json()
    other = (await _create(client, bob, "Bureau")).json()

    # Alice rejoint aussi le foyer de Bob.
    r = await client.post(
        "/households/join", json={"invite_code": other["invite_code"]}, headers=alice
    )
    assert r.status_code == 200

    listed = (await client.get("/households", headers=alice)).json()
    assert [x["id"] for x in listed] == [first["id"], second["id"], other["id"]]
    assert [x["id"] for x in (await client.get("/households", headers=bob)).json()] == [other["id"]]


async def test_get_requires_membership(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    hh = (await _create(client, alice)).json()
    assert (await client.get(f"/households/{hh['id']}", headers=bob)).status_code == 404
    assert (await client.post(f"/households/{hh['id']}/leave", headers=bob)).status_code == 404


async def test_join(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    code = (await _create(client, alice)).json()["invite_code"]

    r = await client.post("/households/join", json={"invite_code": code}, headers=bob)
    assert r.status_code == 200
    assert {m["email"] for m in r.json()["members"]} == {"alice@example.com", "bob@example.com"}
    assert (
        await client.post("/households/join", json={"invite_code": code}, headers=bob)
    ).status_code == 409


async def test_join_bad_code_404(client, auth_headers):
    h = await auth_headers()
    r = await client.post("/households/join", json={"invite_code": "zzzzzzzz"}, headers=h)
    assert r.status_code == 404


async def test_leave_one_keeps_the_others(client, auth_headers):
    alice = await auth_headers()
    first = (await _create(client, alice, "Maison")).json()
    second = (await _create(client, alice, "Vacances")).json()

    assert (await client.post(f"/households/{first['id']}/leave", headers=alice)).status_code == 204
    assert [x["id"] for x in (await client.get("/households", headers=alice)).json()] == [
        second["id"]
    ]


async def test_leave_keeps_household_until_last_member(client, auth_headers, engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    created = (await _create(client, alice)).json()
    hid = created["id"]
    await client.post("/households/join", json={"invite_code": created["invite_code"]}, headers=bob)
    await client.post(f"/households/{hid}/shop-items", json={"name": "Lait"}, headers=alice)

    assert (await client.post(f"/households/{hid}/leave", headers=alice)).status_code == 204
    assert (await client.get(f"/households/{hid}", headers=alice)).status_code == 404
    assert len((await client.get(f"/households/{hid}/shop-items", headers=bob)).json()) == 1

    assert (await client.post(f"/households/{hid}/leave", headers=bob)).status_code == 204
    # Le foyer et ses articles ont disparu.
    r = await client.post(
        "/households/join", json={"invite_code": created["invite_code"]}, headers=alice
    )
    assert r.status_code == 404
    async with AsyncSession(engine) as s:
        assert await s.scalar(select(func.count()).select_from(ShopItem)) == 0
        assert await s.get(Household, hid) is None
