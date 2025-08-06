from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.modules.users.schemas import CreateUserScheme
from src.storages.sql.models import User, UserRole


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_or_create(self, user_create: CreateUserScheme) -> User:
        user = await self.read_by_innohassle_id(user_create.innohassle_id)
        if user is not None:
            return user
        return await self.create(user_create)

    async def create(self, user_create: CreateUserScheme) -> User:
        user = User.model_validate(user_create, from_attributes=True)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User):
        await self.session.delete(user)
        await self.session.commit()

    async def read_by_innohassle_id(self, innohassle_id: str) -> User | None:
        query = select(User).where(User.innohassle_id == innohassle_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def read_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def change_role_of_user(self, user: User, role: UserRole) -> User:
        user.role = role
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
