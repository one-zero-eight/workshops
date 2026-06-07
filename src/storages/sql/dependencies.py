from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    url=settings.db_url.get_secret_value(),
    pool_pre_ping=True,
    pool_timeout=10,
    # echo=True
)

Session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    # ensures that db is opened and closed per request
    async with Session() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
