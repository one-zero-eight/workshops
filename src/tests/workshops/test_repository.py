from datetime import datetime, timedelta
import pytest
import pytest_asyncio

from src.modules.workshops.enums import WorkshopEnum, CheckInEnum
from src.storages.sql.models.users import User
from src.storages.sql.models.workshops import Workshop

# TODO: ENhance test and recheck them
# TODO: Add integrational tests (how?)


class TestWorkshops:
    @pytest.mark.asyncio
    async def test_create_workshop(self, add_workshop_and_clean):
        assert add_workshop_and_clean.id is not None
        assert add_workshop_and_clean.name == "name"

    @pytest.mark.asyncio
    async def test_get_all_workshops(self, getWorkshopRepository, add_workshop_and_clean):
        repo = getWorkshopRepository

        workshop = add_workshop_and_clean
        workshops = await repo.get_all_workshops()

        assert workshop in workshops
        # assert workshops[-1].dtstart/ == workshop.dtstart

    @pytest.mark.asyncio
    async def test_get_workshop_by_id(self, getWorkshopRepository, add_workshop_and_clean):
        repo = getWorkshopRepository

        added_workshop = add_workshop_and_clean
        workshop = await repo.get_workshop_by_id(added_workshop.id)

        assert added_workshop == workshop

    @pytest.mark.asyncio
    async def test_update_workshop(self, update_workshop_data, getWorkshopRepository, add_workshop_and_clean):
        repo = getWorkshopRepository

        added_workshop = add_workshop_and_clean
        workshop_updated, status = await repo.update_workshop(added_workshop.id, update_workshop_data)

        assert status == WorkshopEnum.UPDATED
        assert workshop_updated.name == update_workshop_data.name
        assert added_workshop.id == workshop_updated.id

    @pytest.mark.asyncio
    async def test_change_active_status_workshop(self, getWorkshopRepository, add_workshop_and_clean):
        repo = getWorkshopRepository

        added_workshop = add_workshop_and_clean
        workshop_changed = await repo.change_active_status_workshop(added_workshop.id, True)

        assert workshop_changed.is_active == True

    @pytest.mark.asyncio
    async def test_delete_workshop(self, getWorkshopRepository, add_workshop_and_clean):
        repo = getWorkshopRepository

        added_workshop = add_workshop_and_clean
        status = await repo.delete_workshop(added_workshop.id)

        assert status == WorkshopEnum.DELETED


class TestWorkshopCheckIn:
    "TODO: Need to add all possible (failed) cases for testing"

    @pytest_asyncio.fixture(autouse=True)
    async def _setup_data(self, add_checkin_and_clean):
        self.user, self.workshop = add_checkin_and_clean

    @pytest.mark.asyncio
    async def test_create_checkIn_success(self):
        assert self.workshop.remain_places == self.workshop.capacity - 1  # type: ignore

    @pytest.mark.asyncio
    async def test_create_checkIn_not_exists(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository, getWorkshopRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, f"{workshop.id}_wrong")

        assert status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)

    @pytest.mark.asyncio
    async def test_create_checkIn_not_active(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        workshop.is_active = False

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)
        assert status == CheckInEnum.NOT_ACTIVE

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)

    @pytest.mark.asyncio
    async def test_create_checkIn_no_places(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        workshop.remain_places = 0

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)
        assert status == CheckInEnum.NO_PLACES

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)

    @pytest.mark.asyncio
    async def test_create_checkIn_invalid_time(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        workshop.dtstart = datetime.now() + timedelta(days=360 * 4)

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)
        assert status == CheckInEnum.INVALID_TIME

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)

    @pytest.mark.asyncio
    async def test_create_checkIn_already_checked_in(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)

        assert status == CheckInEnum.ALREADY_CHECKED_IN

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)

    @pytest.mark.asyncio
    async def test_create_checkIn_overlapping_workshops(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository, create_workshop_data, getWorkshopRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean
        status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)

        overlapping_data = create_workshop_data.copy()
        overlapping_data.dtstart = workshop.dtstart
        overlapping_data.dtend = workshop.dtend
        overlapping_data.name = "Name"
        overlapping_data.is_active = True
        # overlapping_data["dtstart"] = workshop.dtstart
        # overlapping_data["dtend"] = workshop.dtend
        # overlapping_data["name"] = "Overlapping Workshop"

        second_workshop, status = await getWorkshopRepository.create_workshop(overlapping_data)
        assert status == WorkshopEnum.CREATED

        status = await getWorkshopCheckinRepository.create_checkIn(user.id, second_workshop.id)

        assert status == CheckInEnum.OVERLAPPING_WORKSHOPS

        await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)
        await getWorkshopRepository.delete_workshop(second_workshop.id)

    @pytest.mark.asyncio
    async def test_exists_checkin(self, getWorkshopCheckinRepository):
        exists = await getWorkshopCheckinRepository.exists_checkin(self.user.id, self.workshop.id)
        assert exists == True

    @pytest.mark.asyncio
    async def test_get_checked_in_workshops_for_user(self, getWorkshopCheckinRepository):
        workshops = await getWorkshopCheckinRepository.get_checked_in_workshops_for_user(self.user.id)
        assert self.workshop in workshops

    @pytest.mark.asyncio
    async def test_get_checked_in_users_for_workshop(self, getWorkshopCheckinRepository):
        users = await getWorkshopCheckinRepository.get_checked_in_users_for_workshop(self.workshop.id)
        assert self.user in users

    @pytest.mark.asyncio
    async def test_remove_checkIn_success(self, getWorkshopCheckinRepository):
        await getWorkshopCheckinRepository.create_checkIn(self.user.id, self.workshop.id)
        remove_status = await getWorkshopCheckinRepository.remove_checkIn(self.user.id, self.workshop.id)
        assert remove_status == CheckInEnum.SUCCESS

    @pytest.mark.asyncio
    async def test_remove_checkIn_workshop_not_exists(self, add_workshop_and_clean, add_user_and_clean, getWorkshopCheckinRepository):
        workshop = add_workshop_and_clean
        user = add_user_and_clean

        status = await getWorkshopCheckinRepository.remove_checkIn(user.id, f"{workshop.id}_wrong")

        assert status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST