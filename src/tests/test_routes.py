from httpx import AsyncClient


async def test_root(async_client: AsyncClient):
    response = await async_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert response.url == "http://test/docs"
