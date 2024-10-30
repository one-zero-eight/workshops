from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.workshops.schemes import ViewWorkshopScheme
from src.storages.sql.models.workshops import CheckIn, Workshop


class SqlWorkshopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_list_by_user_id(self, user_id: int) -> list[ViewWorkshopScheme]:
        request = select(Workshop).join(Workshop.check_ins).where(CheckIn.user_id == user_id)
        workshops = await self.session.execute(request)
        workshops = workshops.scalars()
        return [ViewWorkshopScheme.model_validate(wk, from_attributes=True) for wk in workshops]

    async def get_by_id(self, workshop_id: int) -> ViewWorkshopScheme | None:
        request = select(Workshop).where(workshop_id=workshop_id)
        workshop = await self.session.execute(request)
        workshop = workshop.scalar()
        if workshop is not None:
            return ViewWorkshopScheme.model_validate(workshop, from_attributes=True)

    async def update_remain_places(self, workshop_id: int, delta: int) -> None:
        request = (
            update(Workshop)
            .where(Workshop.id == workshop_id)
            .values({Workshop.remain_places: Workshop.remain_places + delta})
        )
        await self.session.execute(request)


class SqlCheckInRepository:
    def __init__(self, session: AsyncSession, workshops_repository: SqlWorkshopRepository) -> None:
        self.session = session
        self.workshops_repository = workshops_repository

    async def create(self, workshop_id: int, user_id: int) -> bool:
        workshop = await self.workshops_repository.get_by_id(workshop_id)
        if workshop is None or workshop.remain_places == 0:
            return False
        request = insert(CheckIn).values(workshop_id=workshop_id, user_id=user_id)
        await self.session.execute(request)
        await self.workshops_repository.update_remain_places(workshop_id, -1)
        await self.session.commit()
        return True

    async def delete(self, workshop_id: int, user_id: int) -> bool:
        workshop = await self.workshops_repository.get_by_id(workshop_id)
        if workshop is None:
            return False
        request = delete(CheckIn).where(workshop_id=workshop_id, user_id=user_id)
        await self.session.execute(request)
        await self.workshops_repository.update_remain_places(workshop_id, 1)
        await self.session.commit()
        return True
