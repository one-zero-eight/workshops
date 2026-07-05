from fastapi import status
from httpx import AsyncClient

from src.modules.events.enums import EventEnum
from src.storages.sql.models import CreateEvent, Event, EventStatus, UpdateEvent, User


async def test_add_event_success(admin_authenticated_client: AsyncClient, event_data_to_create: CreateEvent):
    data = event_data_to_create.model_dump(mode="json", exclude_none=True)
    response = await admin_authenticated_client.post("/events/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    resp_json = response.json()
    assert resp_json["english_name"] == data["english_name"]
    assert resp_json["english_description"] == data["english_description"]
    assert resp_json["status"] == EventStatus.DRAFT.value


async def test_add_event_fail(admin_authenticated_client: AsyncClient, event_data_to_create: CreateEvent):
    # Simulate failure by sending incomplete data
    data = event_data_to_create.model_dump(mode="json", exclude_none=True)
    data.pop("english_name")
    response = await admin_authenticated_client.post("/events/", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_get_all_events(
    authenticated_client: AsyncClient,
    superadmin_authenticated_client: AsyncClient,
    already_created_event: Event,
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    response = await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    assert response.status_code == status.HTTP_200_OK

    response = await authenticated_client.get("/events/")
    assert response.status_code == status.HTTP_200_OK
    events = response.json()
    assert isinstance(events, list)
    assert any(e["id"] == already_created_event.id for e in events)


async def test_get_all_events_filters_unapproved(
    authenticated_client: AsyncClient,
    already_created_event: Event,
):
    response = await authenticated_client.get("/events/")
    assert response.status_code == status.HTTP_200_OK
    # Normal user should not see draft event since they are not the creator (creator is in fixture but `already_created_event` fixture uses the same `user` so they *would* see it if we pass status!)
    # But GET /events without status query parameter only returns approved.
    assert all(e["id"] != already_created_event.id for e in response.json())


async def test_update_event_success(
    admin_authenticated_client: AsyncClient,
    already_created_event: Event,
    event_data_to_update: UpdateEvent,
):
    data = event_data_to_update.model_dump(mode="json", exclude_none=True)
    response = await admin_authenticated_client.patch(f"/events/{already_created_event.id}", json=data)
    assert response.status_code == status.HTTP_200_OK
    resp_json = response.json()
    assert resp_json["english_name"] == data["english_name"]
    assert resp_json["english_description"] == data["english_description"]
    assert resp_json["status"] == EventStatus.DRAFT.value


async def test_update_event_not_found(admin_authenticated_client: AsyncClient, event_data_to_update: UpdateEvent):
    data = event_data_to_update.model_dump(mode="json", exclude_none=True)
    response = await admin_authenticated_client.patch("/events/nonexistent_id", json=data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_approve_event_success(
    superadmin_authenticated_client: AsyncClient,
    already_created_event: Event,
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    response = await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == EventStatus.APPROVED.value


async def test_approve_event_forbidden(
    admin_authenticated_client: AsyncClient,
    already_created_event: Event,
):
    await admin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    # Not superadmin
    response = await admin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_approve_event_not_found(superadmin_authenticated_client: AsyncClient):
    response = await superadmin_authenticated_client.post("/events/nonexistent_id/approve")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_event_resets_approval(
    superadmin_authenticated_client: AsyncClient,
    already_created_event: Event,
    event_data_to_update: UpdateEvent,
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    response = await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == EventStatus.APPROVED.value

    data = event_data_to_update.model_dump(mode="json", exclude_none=True)
    response = await superadmin_authenticated_client.patch(f"/events/{already_created_event.id}", json=data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == EventStatus.DRAFT.value


async def test_delete_event_success(admin_authenticated_client: AsyncClient, already_created_event: Event):
    response = await admin_authenticated_client.delete(f"/events/{already_created_event.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == EventEnum.DELETED.value


async def test_delete_event_fail(admin_authenticated_client: AsyncClient):
    response = await admin_authenticated_client.delete("/events/nonexistent_id")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_register_user_success(
    authenticated_client: AsyncClient, already_created_event: Event, superadmin_authenticated_client: AsyncClient
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    response = await authenticated_client.post(f"/events/{already_created_event.id}/registrations")
    assert response.status_code == status.HTTP_200_OK


async def test_register_user_fail(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/events/nonexistent_id/registrations")
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


async def test_unregister_user_success(
    authenticated_client: AsyncClient, already_created_event: Event, superadmin_authenticated_client: AsyncClient
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    await authenticated_client.post(f"/events/{already_created_event.id}/registrations")
    response = await authenticated_client.delete(f"/events/{already_created_event.id}/registrations")
    assert response.status_code == status.HTTP_200_OK


async def test_unregister_user_not_found(authenticated_client: AsyncClient, already_created_event: Event):
    response = await authenticated_client.delete(f"/events/{already_created_event.id}/registrations")
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


async def test_get_all_registrations_empty(authenticated_client: AsyncClient, already_created_event: Event):
    response = await authenticated_client.get(f"/events/{already_created_event.id}/registrations")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_get_all_registrations(
    authenticated_client: AsyncClient,
    already_created_event: Event,
    user: User,
    superadmin_authenticated_client: AsyncClient,
):
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/publish")
    await superadmin_authenticated_client.post(f"/events/{already_created_event.id}/approve")
    await authenticated_client.post(f"/events/{already_created_event.id}/registrations")
    response = await authenticated_client.get(f"/events/{already_created_event.id}/registrations")
    assert response.status_code == status.HTTP_200_OK
    # Because user is not admin, email might be redacted depending on ViewUserScheme, but user_id should be there
    assert any(u["innohassle_id"] == user.innohassle_id for u in response.json())
