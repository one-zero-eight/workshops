from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncGenerator:
    async with request.app.state.storage.sessionmaker() as session:
        yield session
        await session.close()


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
