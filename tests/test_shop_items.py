async def _household(client, h, name="Maison"):
    return (await client.post("/household", json={"name": name}, headers=h)).json()


async def test_requires_household(client, auth_headers):
    h = await auth_headers()
    assert (await client.get("/shop-items", headers=h)).status_code == 404
    assert (await client.post("/shop-items", json={"name": "Lait"}, headers=h)).status_code == 404


async def test_create_and_list(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    r = await client.post("/shop-items", json={"name": " Lait "}, headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Lait"
    assert body["quantity"] == "1"
    assert body["category"] is None
    assert body["checked"] is False
    assert body["household_id"] == hh["id"]
    assert body["added_by"] == hh["members"][0]["id"]
    assert (await client.get("/shop-items", headers=h)).json() == [body]


async def test_validation(client, auth_headers):
    h = await auth_headers()
    await _household(client, h)
    for payload in (
        {"name": "  "},
        {"name": "x" * 101},
        {"name": "a", "quantity": "q" * 51},
        {"name": "a", "category": "c" * 101},
    ):
        assert (await client.post("/shop-items", json=payload, headers=h)).status_code == 422


async def test_ordering(client, auth_headers):
    h = await auth_headers()
    await _household(client, h)
    ids = {}
    for name in ("a", "b", "c"):
        ids[name] = (await client.post("/shop-items", json={"name": name}, headers=h)).json()["id"]
    await client.patch(f"/shop-items/{ids['c']}", json={"checked": True}, headers=h)
    order = [i["id"] for i in (await client.get("/shop-items", headers=h)).json()]
    assert order == [ids["b"], ids["a"], ids["c"]]


async def test_update_and_delete(client, auth_headers):
    h = await auth_headers()
    await _household(client, h)
    iid = (await client.post("/shop-items", json={"name": "Lait"}, headers=h)).json()["id"]

    r = await client.patch(
        f"/shop-items/{iid}",
        json={"quantity": "2L", "category": "Boissons", "checked": True},
        headers=h,
    )
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["quantity"], r.json()["category"], r.json()["checked"]) == (
        "Lait",
        "2L",
        "Boissons",
        True,
    )
    r = await client.patch(f"/shop-items/{iid}", json={"category": None}, headers=h)
    assert r.json()["category"] is None
    assert r.json()["quantity"] == "2L"
    assert (
        await client.patch(f"/shop-items/{iid}", json={"name": None}, headers=h)
    ).status_code == 422

    assert (await client.delete(f"/shop-items/{iid}", headers=h)).status_code == 204
    assert (await client.delete(f"/shop-items/{iid}", headers=h)).status_code == 404
    assert (
        await client.patch("/shop-items/999999", json={"name": "x"}, headers=h)
    ).status_code == 404


async def test_clear_checked(client, auth_headers):
    h = await auth_headers()
    await _household(client, h)
    ids = [
        (await client.post("/shop-items", json={"name": n}, headers=h)).json()["id"]
        for n in ("a", "b")
    ]
    await client.patch(f"/shop-items/{ids[0]}", json={"checked": True}, headers=h)

    assert (await client.delete("/shop-items", headers=h)).status_code == 422
    assert (await client.delete("/shop-items?checked=false", headers=h)).status_code == 422
    assert len((await client.get("/shop-items", headers=h)).json()) == 2

    assert (await client.delete("/shop-items?checked=true", headers=h)).status_code == 204
    assert [i["id"] for i in (await client.get("/shop-items", headers=h)).json()] == [ids[1]]


async def test_isolation_between_households(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    await _household(client, alice, "A")
    await _household(client, bob, "B")
    aid = (await client.post("/shop-items", json={"name": "Lait"}, headers=alice)).json()["id"]
    await client.post("/shop-items", json={"name": "Pain", "checked": True}, headers=bob)

    assert [i["name"] for i in (await client.get("/shop-items", headers=bob)).json()] == ["Pain"]
    assert (
        await client.patch(f"/shop-items/{aid}", json={"name": "x"}, headers=bob)
    ).status_code == 404
    assert (await client.delete(f"/shop-items/{aid}", headers=bob)).status_code == 404
    await client.patch(f"/shop-items/{aid}", json={"checked": True}, headers=alice)
    assert (await client.delete("/shop-items?checked=true", headers=bob)).status_code == 204
    assert len((await client.get("/shop-items", headers=alice)).json()) == 1
