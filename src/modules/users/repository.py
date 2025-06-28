from sqlmodel import select


from src.storages.sql.models.users import User


from sqlmodel import select

from src.storages.sql.models.users import User
from src.modules.users.schemes import CreateUserScheme, UserRole

from sqlalchemy.ext.asyncio import AsyncSession
from src.logging import logger


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_create: CreateUserScheme) -> User:
        user = User.model_validate(user_create, from_attributes=True)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def delete(self, user: User):
        await self.session.delete(user)
        await self.session.commit()

    async def read_by_id(self, user_id: str) -> User | None:
        logger.info(user_id)
        query = select(User).where(User.id == user_id)
        user = await self.session.execute(query)
        user = user.scalars().first()
        if user is None:
            logger.warning("User not found")
        return user

    async def read_id_by_innohassle_id(self, innohassle_id: str) -> str | None:
        query = select(User.id).where(User.innohassle_id == innohassle_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def change_role_of_user(self, user_id: str, role: str) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()

        if not user:
            return None

        if role == "admin":
            user.role = UserRole.admin
        else:
            user.role = UserRole.user

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user
