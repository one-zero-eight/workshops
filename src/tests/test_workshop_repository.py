from datetime import UTC, datetime, timedelta

from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.modules.workshops.repository import WorkshopRepository
from src.modules.workshops.schemas import CreateWorkshopScheme, UpdateWorkshopScheme
from src.storages.sql.models import User, Workshop


async def test_create_workshop(
    workshop_repository: WorkshopRepository,
    workshop_data_to_create: CreateWorkshopScheme,
):
    workshop, status = await workshop_repository.create(workshop_data_to_create)
    assert status == WorkshopEnum.CREATED
    assert workshop is not None
    assert workshop.id is not None
    assert workshop.name == workshop_data_to_create.name


async def test_get_all_workshops(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
):
    workshops = await workshop_repository.get_all()
    assert already_created_workshop in workshops


async def test_get_workshop_by_id(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
):
    got_workshop = await workshop_repository.get(already_created_workshop.id)
    assert already_created_workshop == got_workshop


async def test_update_workshop(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    workshop_data_to_update: UpdateWorkshopScheme,
):
    workshop_updated, status = await workshop_repository.update(already_created_workshop.id, workshop_data_to_update)
    assert status == WorkshopEnum.UPDATED
    assert workshop_updated is not None
    assert workshop_updated.name == workshop_data_to_update.name
    assert workshop_updated.id == already_created_workshop.id


async def test_change_active_status_workshop(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
):
    workshop_changed = await workshop_repository.set_active(already_created_workshop.id, True)
    assert workshop_changed is not None
    assert workshop_changed.is_active
    workshop_changed = await workshop_repository.set_active(already_created_workshop.id, False)
    assert workshop_changed is not None
    assert not workshop_changed.is_active


async def test_delete_workshop(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
):
    status = await workshop_repository.delete(already_created_workshop.id)
    assert status == WorkshopEnum.DELETED


async def test_check_in(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS
    assert already_created_workshop.remain_places == (already_created_workshop.capacity - 1)

    status = await workshop_repository.check_out(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS
    assert already_created_workshop.remain_places == already_created_workshop.capacity


async def test_check_in_workshop_not_exists(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, f"{already_created_workshop.id}_wrong")
    assert status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST


async def test_check_in_workshop_not_active(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    await workshop_repository.set_active(already_created_workshop.id, False)
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.NOT_ACTIVE


async def test_check_in_no_places(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    await workshop_repository.update(already_created_workshop.id, UpdateWorkshopScheme(capacity=0))
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.NO_PLACES


async def test_check_in_invalid_time(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    await workshop_repository.update(
        already_created_workshop.id,
        UpdateWorkshopScheme(
            dtstart=datetime.now(UTC) + timedelta(days=360 * 4),
            dtend=datetime.now(UTC) + timedelta(days=360 * 4, hours=1),
        ),
    )
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.INVALID_TIME


async def test_check_in_already_checked_in(
    already_created_workshop: Workshop,
    workshop_repository: WorkshopRepository,
    user: User,
):
    await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.ALREADY_CHECKED_IN


async def test_check_in_overlapping_workshops(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS

    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.ALREADY_CHECKED_IN

    second_workshop, status = await workshop_repository.create(
        CreateWorkshopScheme(
            name="Name",
            description="Description",
            dtstart=already_created_workshop.dtstart,
            dtend=already_created_workshop.dtend,
            is_active=True,
            place="Place",
        )
    )
    assert second_workshop is not None
    assert status == WorkshopEnum.CREATED

    status = await workshop_repository.check_in(user.innohassle_id, second_workshop.id)

    assert status == CheckInEnum.OVERLAPPING_WORKSHOPS

    await workshop_repository.check_out(user.innohassle_id, already_created_workshop.id)
    await workshop_repository.delete(second_workshop.id)


async def test_is_checked_in(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS

    checked_in = await workshop_repository.is_checked_in(user.innohassle_id, already_created_workshop.id)
    assert checked_in

    status = await workshop_repository.check_out(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS

    checked_in = await workshop_repository.is_checked_in(user.innohassle_id, already_created_workshop.id)
    assert not checked_in


async def test_get_checked_in_workshops(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS

    workshops = await workshop_repository.get_checked_in_workshops(user.innohassle_id)
    assert already_created_workshop in workshops


async def test_get_checked_in_users(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_in(user.innohassle_id, already_created_workshop.id)
    assert status == CheckInEnum.SUCCESS

    users = await workshop_repository.get_checked_in_users(already_created_workshop.id)
    assert user in users


async def test_check_out_workshop_not_exists(
    workshop_repository: WorkshopRepository,
    already_created_workshop: Workshop,
    user: User,
):
    status = await workshop_repository.check_out(user.innohassle_id, f"{already_created_workshop.id}_wrong")
    assert status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST
