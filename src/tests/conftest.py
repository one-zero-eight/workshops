from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import pytest_asyncio
from src.api import app
from src.config import settings
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.modules.workshops.enums import WorkshopEnum, CheckInEnum
from src.modules.workshops.repository import WorkshopRepository, CheckInRepository
from src.modules.users.repository import UsersRepository
from src.modules.workshops.schemes import CreateWorkshopScheme, UpdateWorkshopScheme
from src.modules.users.schemes import CreateUserScheme
from src.storages.sql.models.users import User

from src.storages.sql.models.users import UserRole
# TODO: Need to rewrite scope of fixtures as now everything is created each time it's kinda bad


@pytest_asyncio.fixture(loop_scope="function")
async def session_db_connection():
    engine = create_async_engine(
        # url="sqlite+aiosqlite:///:memory:"
        url=settings.database_uri,
        # echo=True
    )

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="function")
async def create_user_data():
    user = CreateUserScheme(innohassle_id="some_innohassle_id", email="user@example.com")
    return user


@pytest_asyncio.fixture(loop_scope="function")
async def create_workshop_data():
    create_data = CreateWorkshopScheme(name="name", description="description",
                                       place="place", dtstart=datetime.now() + timedelta(minutes=1), dtend=datetime.now() + timedelta(days=1), is_active=False)
    return create_data


@pytest_asyncio.fixture(loop_scope="function")
async def update_workshop_data():
    update_data = UpdateWorkshopScheme(name="name_updated", description="description_updated",
                                       place="place_updated", dtstart=datetime.now() + timedelta(minutes=1), dtend=datetime.now() + timedelta(days=1))
    return update_data


@pytest_asyncio.fixture(loop_scope="function")
async def getWorkshopRepository(session_db_connection):
    return WorkshopRepository(session_db_connection)  # type: ignore


@pytest_asyncio.fixture(loop_scope="function")
async def getWorkshopCheckinRepository(session_db_connection, getWorkshopRepository):
    return CheckInRepository(session_db_connection, getWorkshopRepository)


@pytest_asyncio.fixture(loop_scope="function")
async def getUserRepository(session_db_connection):
    return UsersRepository(session_db_connection)


@pytest_asyncio.fixture(loop_scope="function")
async def add_user_and_clean(create_user_data, getUserRepository):
    user = await getUserRepository.create(create_user_data)
    assert user is not None
    yield user

    await getUserRepository.delete(user)


@pytest_asyncio.fixture(loop_scope="function")
async def add_workshop_and_clean(create_workshop_data, getWorkshopRepository):
    workshop, status = await getWorkshopRepository.create_workshop(create_workshop_data)
    assert status == WorkshopEnum.CREATED
    yield workshop

    await getWorkshopRepository.delete_workshop(workshop.id)


@pytest_asyncio.fixture(loop_scope="function")
async def add_user_and_workshop_clean(add_workshop_and_clean, add_user_and_clean):
    workshop = add_workshop_and_clean
    user = add_user_and_clean
    return workshop, user


@pytest_asyncio.fixture(loop_scope="function")
async def add_checkin_and_clean(getWorkshopCheckinRepository, add_workshop_and_clean, getWorkshopRepository, add_user_and_clean):
    workshop = add_workshop_and_clean
    workshop.is_active = True

    user = add_user_and_clean

    status = await getWorkshopCheckinRepository.create_checkIn(user.id, workshop.id)

    assert status == CheckInEnum.SUCCESS

    yield user, workshop

    await getWorkshopCheckinRepository.remove_checkIn(user.id, workshop.id)


@pytest_asyncio.fixture(loop_scope="function")
async def admin_dep(create_user_data):
    return create_user_data


@pytest_asyncio.fixture(loop_scope="function")
async def current_user_id_dep():
    return "some_user_id"


@pytest_asyncio.fixture(loop_scope="function")
async def get_client():
    client = TestClient(app.app)
    return client
