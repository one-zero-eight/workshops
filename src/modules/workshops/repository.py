import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.schemes import ViewUserScheme
from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.modules.workshops.schemes import CreateWorkshopScheme, ViewWorkshopScheme
from src.storages.sql.models.users import User
from src.storages.sql.models.workshops import CheckIn, Workshop


class SqlWorkshopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, workshop: CreateWorkshopScheme) -> tuple[ViewWorkshopScheme | None, WorkshopEnum]:
        to_insert = workshop.model_dump()
        to_insert["remain_places"] = workshop.capacity
        query = insert(Workshop).values(**to_insert).on_conflict_do_nothing().returning(Workshop)
        workshop = await self.session.execute(query)
        workshop = workshop.scalar()
        await self.session.commit()
        if workshop is not None:
            return ViewWorkshopScheme.model_validate(workshop, from_attributes=True), WorkshopEnum.CREATED
        return None, WorkshopEnum.ALIAS_ALREADY_EXISTS

    async def read_all(self) -> list[ViewWorkshopScheme]:
        query = select(Workshop)
        workshops = await self.session.execute(query)
        workshops = workshops.scalars()
        return [ViewWorkshopScheme.model_validate(wk, from_attributes=True) for wk in workshops]

    async def get_by_id(self, workshop_id: int) -> ViewWorkshopScheme | None:
        request = select(Workshop).where(Workshop.id == workshop_id)
        workshop = await self.session.execute(request)
        workshop = workshop.scalar()
        if workshop is not None:
            return ViewWorkshopScheme.model_validate(workshop, from_attributes=True)

    async def update_remain_places(self, workshop_id: int, delta: int) -> None:
        query = (
            update(Workshop)
            .where(Workshop.id == workshop_id)
            .values({Workshop.remain_places: Workshop.remain_places + delta})
        )
        await self.session.execute(query)


class SqlCheckInRepository:
    def __init__(self, session: AsyncSession, workshops_repository: SqlWorkshopRepository) -> None:
        self.session = session
        self.workshops_repository = workshops_repository

    async def exists(self, workshop_id: int, user_id: int) -> bool:
        query = select(CheckIn).where(CheckIn.workshop_id == workshop_id, CheckIn.user_id == user_id)
        result = await self.session.execute(query)
        result = result.scalar()
        return bool(result)

    async def create(self, workshop_id: int, user_id: int) -> CheckInEnum:
        workshop = await self.workshops_repository.get_by_id(workshop_id)
        if workshop is None:
            return CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        if workshop.remain_places == 0:
            return CheckInEnum.NO_PLACES

        exists = await self.exists(workshop_id, user_id)
        if exists:
            return CheckInEnum.ALREADY_CHECKED_IN

        time_now = datetime.datetime.now(tz=None)
        registration_start_time = workshop.dtend.replace(hour=0, minute=0, second=0)

        if time_now < registration_start_time or time_now > workshop.dtstart:
            return CheckInEnum.INVALID_TIME

        request = insert(CheckIn).values(workshop_id=workshop_id, user_id=user_id)
        await self.session.execute(request)
        await self.workshops_repository.update_remain_places(workshop_id, -1)
        await self.session.commit()

        return CheckInEnum.SUCCESS

    async def delete(self, workshop_id: int, user_id: int) -> CheckInEnum:
        exists = await self.exists(workshop_id, user_id)
        if not exists:
            return CheckInEnum.CHECK_IN_DOES_NOT_EXIST

        request = delete(CheckIn).where(CheckIn.workshop_id == workshop_id, CheckIn.user_id == user_id)
        await self.session.execute(request)
        await self.workshops_repository.update_remain_places(workshop_id, 1)
        await self.session.commit()

        return CheckInEnum.SUCCESS

    async def get_check_inned_users_by_workshop_id(self, workshop_id: int) -> list[ViewUserScheme] | None:
        workshop = await self.workshops_repository.get_by_id(workshop_id)
        if workshop is None:
            return
        query = select(CheckIn, User).join(User, User.id == CheckIn.user_id).where(CheckIn.workshop_id == workshop_id)
        results = await self.session.execute(query)
        results = results.all()
        return [ViewUserScheme.model_validate(user, from_attributes=True) for _, user in results]

    async def get_check_inned_workshops_by_user_id(self, user_id: int) -> list[ViewWorkshopScheme]:
        query = (
            select(CheckIn, Workshop)
            .join(Workshop, Workshop.id == CheckIn.workshop_id)
            .where(CheckIn.user_id == user_id)
        )
        results = await self.session.execute(query)
        results = results.all()
        return [ViewWorkshopScheme.model_validate(wk, from_attributes=True) for _, wk in results]
