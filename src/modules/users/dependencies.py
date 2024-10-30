from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DbSessionDep
from src.modules.users.repository import SqlUserRepository


async def get_sql_user_repository(db_session: DbSessionDep) -> SqlUserRepository:
    return SqlUserRepository(db_session)


SqlUserRepositoryDep = Annotated[SqlUserRepository, Depends(get_sql_user_repository)]
