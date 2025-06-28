from fastapi import Depends
from typing import Annotated

from sqlmodel import Session

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
import os
from src.config import settings
from src.logging import logger


engine = create_async_engine(
    url=settings.database_uri,
    # echo=True
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_table():
    logger.info("Accessing db and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    # ensures that db is opened and closed per request
    async with async_session() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
