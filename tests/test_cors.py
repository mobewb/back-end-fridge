async def test_preflight_allowed_origin(client):
    response = await client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_preflight_unknown_origin_rejected(client):
    response = await client.options(
        "/api/v1/products",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers
