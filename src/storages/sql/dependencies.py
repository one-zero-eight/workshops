
from fastapi import Depends
from typing import Annotated

from sqlmodel import Session

# from src.api.lifespan import get_session
# from src.modules.users.schemes import Users, UserRole,

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
import os


engine = create_async_engine(
    url="postgresql+asyncpg://tomatocoder:macbookspass03@localhost:5432/workshops",
    # url=os.getenv("WURL", "sqlite+aiosqlite:///./tasks.db"),
    echo=True
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_table():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    # ensures that db is opened and closed per request
    async with async_session() as session:
        yield session



DbSessionDep = Annotated[AsyncSession, Depends(get_session)]