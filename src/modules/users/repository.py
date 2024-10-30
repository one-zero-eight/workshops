__all__ = ["SqlUserRepository"]

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.schemes import CreateUserScheme, ViewUserScheme
from src.storages.sql.models import User


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: CreateUserScheme) -> ViewUserScheme:
        created = User(**user.model_dump())
        self.session.add(created)
        await self.session.commit()
        return ViewUserScheme.model_validate(created, from_attributes=True)

    async def read(self, user_id: int) -> ViewUserScheme:
        user = await self.session.get(User, user_id)
        return ViewUserScheme.model_validate(user, from_attributes=True)

    async def read_id_by_innohassle_id(self, innohassle_id: str) -> int | None:
        user_id = await self.session.scalar(select(User.id).where(User.innohassle_id == innohassle_id))
        return user_id
