from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.logging_ import logger
from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.storages.sql.models import CreateWorkshop, UpdateWorkshop, User, Workshop, WorkshopCheckin


class WorkshopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, workshop: CreateWorkshop) -> tuple[Workshop | None, WorkshopEnum]:
        if not workshop.capacity:
            workshop.capacity = 10**6
        db_workshop = Workshop.model_validate(workshop.model_dump(exclude_unset=True))

        self.session.add(db_workshop)
        await self.session.commit()
        await self.session.refresh(db_workshop)

        return db_workshop, WorkshopEnum.CREATED

    async def get_all(self, limit: int = 100) -> Sequence[Workshop]:
        query = select(Workshop)
        result = await self.session.execute(query.limit(limit=limit))
        return result.scalars().all()

    async def get(self, workshop_id: str) -> Workshop | None:
        query = select(Workshop).where(Workshop.id == workshop_id)
        result = await self.session.execute(query)
        workshop = result.scalars().first()
        return workshop

    async def update(self, workshop_id: str, workshop_update: UpdateWorkshop) -> tuple[Workshop | None, WorkshopEnum]:
        workshop = await self.get(workshop_id)
        if not workshop:
            return None, WorkshopEnum.WORKSHOP_DOES_NOT_EXIST

        logger.info(f"Updating workshop data. Current data: {workshop}")

        current_data = workshop.model_dump()
        update_data = workshop_update.model_dump(exclude_unset=True)

        merged_data = {**current_data, **update_data}

        Workshop.model_validate(merged_data)

        if workshop_update.capacity is not None:
            # Check if new capacity would be less than current registrations
            current_registrations = workshop.capacity - workshop.remain_places
            if workshop_update.capacity < current_registrations:
                return None, WorkshopEnum.INVALID_CAPACITY_FOR_UPDATE

            workshop.capacity = workshop_update.capacity

        for key, value in update_data.items():
            if value is not None:
                setattr(workshop, key, value)

        await self.session.commit()
        await self.session.refresh(workshop)

        logger.info(f"Updated workshop data. New data: {workshop}")

        return workshop, WorkshopEnum.UPDATED

    async def set_active(self, workshop_id: str, active: bool) -> Workshop | None:
        workshop = await self.get(workshop_id)
        if not workshop:
            return None

        workshop.is_active = active
        # No need to reset remain_places since it's calculated on the fly

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
        # if workshop.dtstart >= datetime.now(UTC) + timedelta(days=1):
        #     return CheckInEnum.INVALID_TIME  # Can check in only 1 day before workshop
        if workshop.dtstart < datetime.now(UTC):
            return CheckInEnum.TIME_IS_OVER

        if await self.is_checked_in(user_id, workshop_id):
            return CheckInEnum.ALREADY_CHECKED_IN

        checked_in_workshops = await self.get_checked_in_workshops(user_id)
        for other in checked_in_workshops:  # block only overlap more than 1 minute
            if other.dtend < workshop.dtstart:
                continue
            elif other.dtstart > workshop.dtend:
                continue
            else:
                overlap_start = max(other.dtstart, workshop.dtstart)
                overlap_end = min(other.dtend, workshop.dtend)
                if overlap_end - overlap_start > timedelta(minutes=1):
                    return CheckInEnum.OVERLAPPING_WORKSHOPS

        checkin = WorkshopCheckin(user_id=user_id, workshop_id=workshop.id)
        self.session.add(checkin)
        await self.session.commit()
        await self.session.refresh(checkin)

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

        return CheckInEnum.SUCCESS

    async def get_checked_in_workshops(self, user_id: str) -> Sequence[Workshop]:
        statement = select(Workshop).join(WorkshopCheckin).where(WorkshopCheckin.user_id == user_id)
        results = await self.session.execute(statement)
        return results.scalars().all()

    async def get_checked_in_users(self, workshop_id: str) -> Sequence[User]:
        statement = select(User).join(WorkshopCheckin).where(WorkshopCheckin.workshop_id == workshop_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def update_image_file_id(
        self, workshop_id: str, image_file_id: str | None
    ) -> tuple[Workshop | None, WorkshopEnum]:
        workshop = await self.get(workshop_id)
        if not workshop:
            return None, WorkshopEnum.WORKSHOP_DOES_NOT_EXIST

        workshop.image_file_id = image_file_id
        await self.session.commit()
        await self.session.refresh(workshop)
        return workshop, WorkshopEnum.UPDATED
