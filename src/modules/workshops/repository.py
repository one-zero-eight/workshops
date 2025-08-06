from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from src.logging_ import logger
from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.modules.workshops.schemas import CreateWorkshopScheme, UpdateWorkshopScheme
from src.storages.sql.models import User, Workshop, WorkshopCheckin


class WorkshopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _update_is_registrable_flag(self):
        now = datetime.now(UTC)
        offset = now + timedelta(days=1)
        stmt = (
            update(Workshop)
            .where(Workshop.dtstart >= datetime.now(UTC))  # type: ignore
            .where(Workshop.dtstart < offset)  # type: ignore
            .values(is_registrable=True)
        )

        await self.session.execute(stmt)

        stmt_disable = (
            update(Workshop)
            .where(Workshop.dtstart < now)  # type: ignore
            .values(is_registrable=False)
        )
        await self.session.execute(stmt_disable)

        await self.session.commit()

    async def create(
        self, workshop: CreateWorkshopScheme
    ) -> tuple[Workshop | None, WorkshopEnum]:
        db_workshop = Workshop.model_validate(workshop)

        self.session.add(db_workshop)
        await self.session.commit()
        await self.session.refresh(db_workshop)

        return db_workshop, WorkshopEnum.CREATED

    async def get_all(self, limit: int = 100) -> Sequence[Workshop]:
        await self._update_is_registrable_flag()

        query = select(Workshop)
        result = await self.session.execute(query.limit(limit=limit))
        return result.scalars().all()

    async def get(self, workshop_id: str) -> Workshop | None:
        query = select(Workshop).where(Workshop.id == workshop_id)
        result = await self.session.execute(query)
        workshop = result.scalars().first()
        return workshop

    async def update(
        self, workshop_id: str, workshop_update: UpdateWorkshopScheme
    ) -> tuple[Workshop | None, WorkshopEnum]:
        workshop = await self.get(workshop_id)
        if not workshop:
            return None, WorkshopEnum.WORKSHOP_DOES_NOT_EXIST

        logger.info(f"Updating workshop data. Current data: {workshop}")
        workshop_dump = workshop_update.model_dump()

        # Check that current number of checked in users is not greater than new capacity
        if (
            workshop_dump["capacity"] != None
            and workshop_dump["capacity"] < workshop.capacity - workshop.remain_places
        ):
            return None, WorkshopEnum.INVALID_CAPACITY_FOR_UPDATE

        # Recalculating the "remain_places" value
        if workshop_dump["capacity"] != None:
            workshop.remain_places = workshop.remain_places - (
                workshop.capacity - workshop_dump["capacity"]
            )

        for key, value in workshop_dump.items():
            if value is not None:
                setattr(workshop, key, value)

        offset = datetime.now(UTC) + timedelta(days=1)
        if workshop.dtstart > offset:
            workshop.is_registrable = False

        self.session.add(workshop)
        await self.session.commit()
        await self.session.refresh(workshop)

        logger.info(f"Updated workshop data. New data: {workshop}")

        return workshop, WorkshopEnum.UPDATED

    async def set_active(
        self, workshop_id: str, active: bool
    ) -> Workshop | None:
        workshop = await self.get(workshop_id)
        if not workshop:
            return None

        workshop.is_active = active
        workshop.remain_places = workshop.capacity  # Reset remaining places to capacity

        self.session.add(workshop)
        await self.session.commit()
        await self.session.refresh(workshop)

        return workshop

    async def delete(self, workshop_id: str) -> WorkshopEnum:
        workshop = await self.get(workshop_id)

        if not workshop:
            return WorkshopEnum.WORKSHOP_DOES_NOT_EXIST

        await self.session.delete(workshop)
        await self.session.commit()

        return WorkshopEnum.DELETED


    async def is_checked_in(self, user_id: str, workshop_id: str) -> bool:
        existing = await self.session.get(WorkshopCheckin, (user_id, workshop_id))
        if existing is not None:
            return True
        return False

    async def check_in(self, user_id: str, workshop_id: str) -> CheckInEnum:
        workshop = await self.get(workshop_id)

        if not workshop:
            return CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        if not workshop.is_active:
            return CheckInEnum.NOT_ACTIVE
        if workshop.remain_places <= 0:
            return CheckInEnum.NO_PLACES
        if workshop.dtstart >= datetime.now(UTC) + timedelta(days=1):
            return CheckInEnum.INVALID_TIME
        if workshop.dtstart < datetime.now(UTC):
            return CheckInEnum.TIME_IS_OVER

        if await self.is_checked_in(user_id, workshop_id):
            return CheckInEnum.ALREADY_CHECKED_IN

        checked_in_workshops = await self.get_checked_in_workshops(user_id)
        for other in checked_in_workshops:
            if other.dtstart <= workshop.dtend and workshop.dtstart <= other.dtend:
                return CheckInEnum.OVERLAPPING_WORKSHOPS

        checkin = WorkshopCheckin(user_id=user_id, workshop_id=workshop.id)
        self.session.add(checkin)
        await self.session.commit()
        await self.session.refresh(checkin)

        workshop.remain_places -= 1
        self.session.add(workshop)
        await self.session.commit()

        return CheckInEnum.SUCCESS

    async def check_out(self, user_id: str, workshop_id: str) -> CheckInEnum:
        workshop = await self.get(workshop_id)

        if not workshop:
            return CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        if not await self.is_checked_in(user_id, workshop_id):
            return CheckInEnum.CHECK_IN_DOES_NOT_EXIST

        checkin = await self.session.get(WorkshopCheckin, (user_id, workshop_id))
        await self.session.delete(checkin)
        await self.session.commit()

        workshop.remain_places += 1
        self.session.add(workshop)
        await self.session.commit()

        return CheckInEnum.SUCCESS

    async def get_checked_in_workshops(
        self, user_id: str
    ) -> Sequence[Workshop]:
        statement = (
            select(Workshop)
            .join(WorkshopCheckin)
            .where(WorkshopCheckin.user_id == user_id)
        )
        results = await self.session.execute(statement)
        return results.scalars().all()

    async def get_checked_in_users(
        self, workshop_id: str
    ) -> Sequence[User]:
        statement = (
            select(User)
            .join(WorkshopCheckin)
            .where(WorkshopCheckin.workshop_id == workshop_id)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
