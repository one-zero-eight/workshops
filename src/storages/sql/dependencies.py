from asyncio import current_task
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    url=settings.db_url.get_secret_value(),
    # echo=True
)

Session = async_scoped_session(
    async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    ),
    scopefunc=current_task,
)


async def get_session():
    # ensures that db is opened and closed per request
    async with Session() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
