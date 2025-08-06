from asyncio import current_task
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from src.api.app import app
from src.api.dependencies import current_user_dep
from src.config import settings
from src.modules.users.repository import UsersRepository
from src.modules.users.schemas import CreateUserScheme
from src.modules.workshops.repository import WorkshopRepository
from src.modules.workshops.schemas import CreateWorkshopScheme, UpdateWorkshopScheme
from src.storages.sql.models import User, UserRole

# --- Set the database URL for testing (isolate it if needed) ---
TEST_DATABASE_URL = settings.db_url.get_secret_value()

# --- Async SQLAlchemy engine using NullPool for isolation ---
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

Session = async_scoped_session(
    async_sessionmaker(expire_on_commit=False),
    scopefunc=current_task,
)


# --- Create all tables at start, drop all at the end ---
@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    """
    Create and drop all tables once per session.
    Ensures a clean test DB environment.
    """

    async with engine.begin() as conn:        
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# --- Session fixture per test function with rollback ---
@pytest.fixture(scope="function")
async def async_session():
    async with engine.begin() as conn:
        async with conn.begin_nested() as transaction:
            async with Session(bind=conn) as session:
                yield session
            await transaction.rollback()


# --- Override FastAPI dependencies to use test session ---
@pytest.fixture()
async def async_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an HTTP client that makes requests directly to the FastAPI app,
    using the test session via dependency override.
    """
    from src.storages.sql.dependencies import get_session

    # Dependency override for `get_session`
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    # Use httpx.AsyncClient with ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_session, None)


# --- Fixtures for authentication ---
@pytest.fixture
async def authenticated_client(async_client: AsyncClient, user: User):
    try:
        app.dependency_overrides[current_user_dep] = lambda: user
        yield async_client
    finally:
        app.dependency_overrides.pop(current_user_dep, None)


@pytest.fixture
async def admin_authenticated_client(async_client: AsyncClient, user: User):
    try:
        app.dependency_overrides[current_user_dep] = lambda: user.model_copy(update={"role": UserRole.admin})
        yield async_client
    finally:
        app.dependency_overrides.pop(current_user_dep, None)


@pytest.fixture
async def workshop_repository(async_session: AsyncSession):
    return WorkshopRepository(async_session)


@pytest.fixture
async def user_repository(async_session: AsyncSession):
    return UsersRepository(async_session)


# --- Fixtures --- #

@pytest.fixture()
async def user(user_repository: UsersRepository):
    created_user = await user_repository.create(
        CreateUserScheme(
            innohassle_id="test_user_id",
            email="test@test.com",
            telegram_username="test_user",
        )
    )
    return created_user


@pytest.fixture
async def workshop_data_to_create():
    return CreateWorkshopScheme(
        name="name",
        description="description",
        place="place",
        dtstart=datetime.now(UTC) + timedelta(minutes=1),
        dtend=datetime.now(UTC) + timedelta(days=1),
        is_active=True,
    )


@pytest.fixture
async def workshop_data_to_update():
    return UpdateWorkshopScheme(
        name="name_updated",
        description="description_updated",
        place="place_updated",
        dtstart=datetime.now(UTC) + timedelta(minutes=1),
        dtend=datetime.now(UTC) + timedelta(days=1),
    )


@pytest.fixture
async def already_created_workshop(
    workshop_repository: WorkshopRepository,
    workshop_data_to_create: CreateWorkshopScheme,
):
    workshop, _ = await workshop_repository.create(workshop_data_to_create)
    assert workshop is not None
    return workshop
