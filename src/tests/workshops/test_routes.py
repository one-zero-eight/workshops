from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest

from src.api import app
import anyio
from src.modules.workshops.dependencies import AdminDep, WorkshopRepositoryDep
from src.modules.workshops.enums import WorkshopEnum

# @pytest.mark.asyncio
# async def test_add_workshop(client, workshop_repo, admin_dep):
#     workshop_repo.create_workshop.return_value = ({"id": "1", "title": "W1", "description": "Test"}, WorkshopEnum.CREATED)

#     async with AsyncClient(base_url="http://test") as ac:
#         res = await ac.post("/api/workshops/", json={"title": "W1", "description": "Test"})

#     assert res.status_code == 201
#     assert res.json()["title"] == "W1"

# def test_get_all_workshops(client):
#     response = awaiclient.get("/api/workshops", headers={"sds": "sdsd"})
#     print(response)
#     assert response.status_code == 200
    
'''
ovigennay stuka
app.dependency_overrides[get_current_user] = override_user
'''