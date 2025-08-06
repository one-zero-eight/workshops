import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.repository import UsersRepository
from src.modules.users.schemas import CreateUserScheme
from src.storages.sql.models import User, UserRole


@pytest.fixture
async def user_data():
    return CreateUserScheme(
        innohassle_id="123",
        email="test@test.com",
        telegram_username="test_user",
    )


async def test_create_user(async_session: AsyncSession, user_data: CreateUserScheme) -> User:
    repo = UsersRepository(async_session)
    user = await repo.create(user_data)
    assert user.innohassle_id == "123"
    assert user.role == UserRole.user
    return user


async def test_change_role_of_user(async_session: AsyncSession, user_data: CreateUserScheme):
    repo = UsersRepository(async_session)
    user = await repo.create(user_data)
    with_changed_role = await repo.change_role_of_user(user, UserRole.user)
    assert with_changed_role.role == UserRole.user
    assert with_changed_role.innohassle_id == user.innohassle_id
