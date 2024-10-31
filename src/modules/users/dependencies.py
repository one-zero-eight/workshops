from typing import Annotated

from fastapi import Depends

from src.modules.users.repository import SqlUserRepository
from src.storages.sql.dependencies import DbSessionDep


async def get_sql_user_repository(db_session: DbSessionDep) -> SqlUserRepository:
    return SqlUserRepository(db_session)


SqlUserRepositoryDep = Annotated[SqlUserRepository, Depends(get_sql_user_repository)]
