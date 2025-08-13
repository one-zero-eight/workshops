from fastapi import status
from httpx import AsyncClient

from src.modules.workshops.enums import WorkshopEnum
from src.storages.sql.models import CreateWorkshop, UpdateWorkshop, User, Workshop


async def test_add_workshop_success(admin_authenticated_client: AsyncClient, workshop_data_to_create: CreateWorkshop):
    data = workshop_data_to_create.model_dump()
    # Convert datetime objects to ISO format strings
    data["dtstart"] = data["dtstart"].isoformat()
    data["dtend"] = data["dtend"].isoformat()
    response = await admin_authenticated_client.post("/workshops/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    resp_json = response.json()
    assert resp_json["name"] == data["name"]
    assert resp_json["description"] == data["description"]


async def test_add_workshop_fail(admin_authenticated_client: AsyncClient, workshop_data_to_create: CreateWorkshop):
    # Simulate failure by sending incomplete data
    data = workshop_data_to_create.model_dump()
    # Convert datetime objects to ISO format strings
    data["dtstart"] = data["dtstart"].isoformat()
    data["dtend"] = data["dtend"].isoformat()
    data.pop("name")
    response = await admin_authenticated_client.post("/workshops/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_all_workshops(authenticated_client: AsyncClient, already_created_workshop: Workshop):
    response = await authenticated_client.get("/workshops/")
    assert response.status_code == status.HTTP_200_OK
    workshops = response.json()
    assert isinstance(workshops, list)
    assert any(w["name"] == already_created_workshop.name for w in workshops)


async def test_update_workshop_success(
    admin_authenticated_client: AsyncClient,
    already_created_workshop: Workshop,
    workshop_data_to_update: UpdateWorkshop,
):
    data = workshop_data_to_update.model_dump()
    # Convert datetime objects to ISO format strings
    data["dtstart"] = data["dtstart"].isoformat()
    data["dtend"] = data["dtend"].isoformat()
    response = await admin_authenticated_client.put(f"/workshops/{already_created_workshop.id}", json=data)
    assert response.status_code == status.HTTP_200_OK
    resp_json = response.json()
    assert resp_json["name"] == data["name"]
    assert resp_json["description"] == data["description"]


async def test_update_workshop_not_found(
    admin_authenticated_client: AsyncClient, workshop_data_to_update: UpdateWorkshop
):
    data = workshop_data_to_update.model_dump()
    # Convert datetime objects to ISO format strings
    data["dtstart"] = data["dtstart"].isoformat()
    data["dtend"] = data["dtend"].isoformat()
    response = await admin_authenticated_client.put("/workshops/nonexistent_id", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_workshop_success(admin_authenticated_client: AsyncClient, already_created_workshop: Workshop):
    response = await admin_authenticated_client.delete(f"/workshops/{already_created_workshop.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == WorkshopEnum.DELETED.value


async def test_delete_workshop_fail(admin_authenticated_client: AsyncClient):
    response = await admin_authenticated_client.delete("/workshops/nonexistent_id")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_checkin_user_success(authenticated_client: AsyncClient, already_created_workshop: Workshop):
    response = await authenticated_client.post(f"/workshops/{already_created_workshop.id}/checkin")
    assert response.status_code == status.HTTP_200_OK


async def test_checkin_user_fail(authenticated_client: AsyncClient):
    # Simulate invalid time or other error by using a non-existent workshop
    response = await authenticated_client.post("/workshops/nonexistent_id/checkin")
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


async def test_checkout_user_success(authenticated_client: AsyncClient, already_created_workshop: Workshop):
    # First check in
    await authenticated_client.post(f"/workshops/{already_created_workshop.id}/checkin")
    response = await authenticated_client.post(f"/workshops/{already_created_workshop.id}/checkout")
    assert response.status_code == status.HTTP_200_OK


async def test_checkout_user_not_found(authenticated_client: AsyncClient, already_created_workshop: Workshop):
    response = await authenticated_client.post(f"/workshops/{already_created_workshop.id}/checkout")
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


async def test_get_all_check_ins_empty(authenticated_client: AsyncClient, already_created_workshop: Workshop):
    response = await authenticated_client.get(f"/workshops/{already_created_workshop.id}/checkins")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_get_all_check_ins(authenticated_client: AsyncClient, already_created_workshop: Workshop, user: User):
    # Check in user
    await authenticated_client.post(f"/workshops/{already_created_workshop.id}/checkin")
    response = await authenticated_client.get(f"/workshops/{already_created_workshop.id}/checkins")
    assert response.status_code == status.HTTP_200_OK
    assert any(u["email"] == user.email for u in response.json())
