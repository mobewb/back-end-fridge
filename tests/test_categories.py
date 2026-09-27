from app.seed import DEFAULT_CATEGORIES


async def test_list_includes_defaults(client, auth_headers):
    h = await auth_headers()
    r = await client.get("/categories", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == len(DEFAULT_CATEGORIES)
    assert all(c["is_default"] for c in body)
    names = {c["name"] for c in body}
    assert {c["name"] for c in DEFAULT_CATEGORIES} == names


async def test_create_custom_category(client, auth_headers):
    h = await auth_headers()
    r = await client.post(
        "/categories", json={"name": "Épices", "emoji": "🌶️", "default_expiry_days": 365}, headers=h
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Épices"
    assert body["is_default"] is False

    r = await client.get("/categories", headers=h)
    assert len(r.json()) == len(DEFAULT_CATEGORIES) + 1


async def test_create_duplicate_rejected(client, auth_headers):
    h = await auth_headers()
    r = await client.post(
        "/categories",
        json={"name": "produits laitiers", "emoji": "🥛", "default_expiry_days": 5},
        headers=h,
    )
    assert r.status_code == 409


async def test_update_and_delete_custom_category(client, auth_headers):
    h = await auth_headers()
    cid = (
        await client.post(
            "/categories",
            json={"name": "Snacks", "emoji": "🍿", "default_expiry_days": 60},
            headers=h,
        )
    ).json()["id"]

    r = await client.patch(f"/categories/{cid}", json={"default_expiry_days": 45}, headers=h)
    assert r.status_code == 200
    assert r.json()["default_expiry_days"] == 45

    assert (await client.delete(f"/categories/{cid}", headers=h)).status_code == 204
    assert (
        await client.patch(f"/categories/{cid}", json={"emoji": "🍟"}, headers=h)
    ).status_code == 404


async def test_update_rejects_duplicate_name(client, auth_headers):
    h = await auth_headers()
    cid = (
        await client.post(
            "/categories",
            json={"name": "Snacks", "emoji": "🍿", "default_expiry_days": 60},
            headers=h,
        )
    ).json()["id"]

    r = await client.patch(f"/categories/{cid}", json={"name": "viande"}, headers=h)
    assert r.status_code == 409


async def test_cannot_modify_default_category(client, auth_headers):
    h = await auth_headers()
    default_id = (await client.get("/categories", headers=h)).json()[0]["id"]
    assert (
        await client.patch(f"/categories/{default_id}", json={"emoji": "🍅"}, headers=h)
    ).status_code == 404
    assert (await client.delete(f"/categories/{default_id}", headers=h)).status_code == 404


async def test_custom_categories_isolated_between_users(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    cid = (
        await client.post(
            "/categories",
            json={"name": "Fait maison", "emoji": "🍳", "default_expiry_days": 3},
            headers=alice,
        )
    ).json()["id"]

    bob_categories = (await client.get("/categories", headers=bob)).json()
    assert cid not in {c["id"] for c in bob_categories}
    assert (
        await client.patch(f"/categories/{cid}", json={"emoji": "🥘"}, headers=bob)
    ).status_code == 404
