async def _household(client, h, name="Maison"):
    return (await client.post("/households", json={"name": name}, headers=h)).json()


def _url(hh, suffix=""):
    return f"/households/{hh['id']}/shop-items{suffix}"


async def test_requires_membership(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    hh = await _household(client, alice)
    assert (await client.get(_url(hh), headers=bob)).status_code == 404
    assert (await client.post(_url(hh), json={"name": "Lait"}, headers=bob)).status_code == 404
    assert (await client.get("/households/999999/shop-items", headers=alice)).status_code == 404


async def test_create_and_list(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    r = await client.post(_url(hh), json={"name": " Lait "}, headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Lait"
    assert body["quantity"] == "1"
    assert body["category"] is None
    assert body["checked"] is False
    assert body["household_id"] == hh["id"]
    assert body["added_by"] == hh["members"][0]["id"]
    assert (await client.get(_url(hh), headers=h)).json() == [body]


async def test_validation(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    for payload in (
        {"name": "  "},
        {"name": "x" * 101},
        {"name": "a", "quantity": "q" * 51},
        {"name": "a", "category": "c" * 101},
    ):
        assert (await client.post(_url(hh), json=payload, headers=h)).status_code == 422


async def test_ordering(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    ids = {}
    for name in ("a", "b", "c"):
        ids[name] = (await client.post(_url(hh), json={"name": name}, headers=h)).json()["id"]
    await client.patch(_url(hh, f"/{ids['c']}"), json={"checked": True}, headers=h)
    order = [i["id"] for i in (await client.get(_url(hh), headers=h)).json()]
    assert order == [ids["b"], ids["a"], ids["c"]]


async def test_update_and_delete(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    iid = (await client.post(_url(hh), json={"name": "Lait"}, headers=h)).json()["id"]

    r = await client.patch(
        _url(hh, f"/{iid}"),
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
    r = await client.patch(_url(hh, f"/{iid}"), json={"category": None}, headers=h)
    assert r.json()["category"] is None
    assert r.json()["quantity"] == "2L"
    assert (
        await client.patch(_url(hh, f"/{iid}"), json={"name": None}, headers=h)
    ).status_code == 422

    assert (await client.delete(_url(hh, f"/{iid}"), headers=h)).status_code == 204
    assert (await client.delete(_url(hh, f"/{iid}"), headers=h)).status_code == 404
    assert (
        await client.patch(_url(hh, "/999999"), json={"name": "x"}, headers=h)
    ).status_code == 404


async def test_clear_checked(client, auth_headers):
    h = await auth_headers()
    hh = await _household(client, h)
    ids = [
        (await client.post(_url(hh), json={"name": n}, headers=h)).json()["id"] for n in ("a", "b")
    ]
    await client.patch(_url(hh, f"/{ids[0]}"), json={"checked": True}, headers=h)

    assert (await client.delete(_url(hh), headers=h)).status_code == 422
    assert (await client.delete(_url(hh) + "?checked=false", headers=h)).status_code == 422
    assert len((await client.get(_url(hh), headers=h)).json()) == 2

    assert (await client.delete(_url(hh) + "?checked=true", headers=h)).status_code == 204
    assert [i["id"] for i in (await client.get(_url(hh), headers=h)).json()] == [ids[1]]


async def test_isolation_between_households(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    ha = await _household(client, alice, "A")
    hb = await _household(client, bob, "B")
    aid = (await client.post(_url(ha), json={"name": "Lait"}, headers=alice)).json()["id"]
    await client.post(_url(hb), json={"name": "Pain", "checked": True}, headers=bob)

    assert [i["name"] for i in (await client.get(_url(hb), headers=bob)).json()] == ["Pain"]
    # Bob ne peut ni cibler le foyer d'Alice, ni atteindre son article via son propre foyer.
    assert (await client.get(_url(ha), headers=bob)).status_code == 404
    assert (
        await client.patch(_url(hb, f"/{aid}"), json={"name": "x"}, headers=bob)
    ).status_code == 404
    assert (await client.delete(_url(hb, f"/{aid}"), headers=bob)).status_code == 404
    await client.patch(_url(ha, f"/{aid}"), json={"checked": True}, headers=alice)
    assert (await client.delete(_url(hb) + "?checked=true", headers=bob)).status_code == 204
    assert len((await client.get(_url(ha), headers=alice)).json()) == 1


async def test_same_user_separate_lists_per_household(client, auth_headers):
    h = await auth_headers()
    h1 = await _household(client, h, "Maison")
    h2 = await _household(client, h, "Vacances")
    await client.post(_url(h1), json={"name": "Lait"}, headers=h)
    await client.post(_url(h2), json={"name": "Crème solaire"}, headers=h)

    assert [i["name"] for i in (await client.get(_url(h1), headers=h)).json()] == ["Lait"]
    assert [i["name"] for i in (await client.get(_url(h2), headers=h)).json()] == ["Crème solaire"]
