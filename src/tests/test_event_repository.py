from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.events.enums import EventEnum, RegistrationEnum
from src.modules.events.repository import EventRepository
from src.storages.sql.models import CreateEvent, Event, EventStatus, UpdateEvent, User


async def test_create_event(
    event_repository: EventRepository,
    event_data_to_create: CreateEvent,
    user: User,
):
    event, status = await event_repository.create(event_data_to_create, created_by=user.innohassle_id)
    assert status == EventEnum.CREATED
    assert event is not None
    assert event.id is not None
    assert event.english_name == event_data_to_create.english_name
    assert event.status == EventStatus.DRAFT


async def test_get_all_events(
    event_repository: EventRepository,
    already_created_event: Event,
):
    await event_repository.approve(already_created_event.id)
    events = await event_repository.get_all(statuses=[EventStatus.APPROVED])
    assert any(event.id == already_created_event.id for event in events)


async def test_get_event_by_id(
    event_repository: EventRepository,
    already_created_event: Event,
):
    got_event = await event_repository.get(already_created_event.id)
    assert already_created_event.id == got_event.id


async def test_update_event(
    event_repository: EventRepository,
    already_created_event: Event,
    event_data_to_update: UpdateEvent,
):
    event_updated, status = await event_repository.update(already_created_event.id, event_data_to_update)
    assert status == EventEnum.UPDATED
    assert event_updated is not None
    assert event_updated.english_name == event_data_to_update.english_name
    assert event_updated.id == already_created_event.id


async def test_approve_event(
    event_repository: EventRepository,
    already_created_event: Event,
):
    await event_repository.publish(already_created_event.id)
    event_approved, status = await event_repository.approve(already_created_event.id)
    assert status == EventEnum.UPDATED
    assert event_approved is not None
    assert event_approved.status == EventStatus.APPROVED


async def test_update_resets_approval(
    event_repository: EventRepository,
    already_created_event: Event,
    event_data_to_update: UpdateEvent,
):
    await event_repository.publish(already_created_event.id)
    event_approved, status = await event_repository.approve(already_created_event.id)
    assert status == EventEnum.UPDATED
    assert event_approved is not None
    assert event_approved.status == EventStatus.APPROVED

    event_updated, status = await event_repository.update(already_created_event.id, event_data_to_update)
    assert status == EventEnum.UPDATED
    assert event_updated is not None
    assert event_updated.status == EventStatus.DRAFT


async def test_delete_event(
    event_repository: EventRepository,
    already_created_event: Event,
):
    status = await event_repository.delete(already_created_event.id)
    assert status == EventEnum.DELETED


async def test_register(
    event_repository: EventRepository,
    already_created_event: Event,
    user: User,
    async_session: AsyncSession,
):
    await event_repository.approve(already_created_event.id)

    status = await event_repository.register(user.innohassle_id, already_created_event.id)
    assert status == RegistrationEnum.SUCCESS

    # get registrations count
    registrations = await event_repository.get_registered_events(user.innohassle_id)
    assert len(registrations) == 1
    assert registrations[0].id == already_created_event.id

    await async_session.refresh(already_created_event)
    assert already_created_event.remain_places == already_created_event.capacity - 1

    status = await event_repository.unregister(user.innohassle_id, already_created_event.id)
    assert status == RegistrationEnum.SUCCESS

    await async_session.refresh(already_created_event)
    assert already_created_event.remain_places == already_created_event.capacity


async def test_register_event_not_exists(
    event_repository: EventRepository,
    already_created_event: Event,
    user: User,
):
    status = await event_repository.register(user.innohassle_id, f"{already_created_event.id}_wrong")
    assert status == RegistrationEnum.EVENT_DOES_NOT_EXIST


async def test_register_event_not_approved(
    event_repository: EventRepository,
    already_created_event: Event,
    user: User,
):
    status = await event_repository.register(user.innohassle_id, already_created_event.id)
    assert status == RegistrationEnum.NOT_ACTIVE


async def test_register_already_registered(
    already_created_event: Event,
    event_repository: EventRepository,
    user: User,
):
    await event_repository.approve(already_created_event.id)
    await event_repository.register(user.innohassle_id, already_created_event.id)
    status = await event_repository.register(user.innohassle_id, already_created_event.id)
    assert status == RegistrationEnum.ALREADY_REGISTERED
