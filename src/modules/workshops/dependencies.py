from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DbSessionDep
from src.modules.workshops.repository import SqlCheckInRepository, SqlWorkshopRepository


async def get_sql_workshop_repository(db_session: DbSessionDep) -> SqlWorkshopRepository:
    return SqlWorkshopRepository(db_session)


SqlWorkshopRepositoryDep = Annotated[SqlWorkshopRepository, Depends(get_sql_workshop_repository)]


async def get_sql_check_in_repository(db_session: DbSessionDep) -> SqlCheckInRepository:
    workshop_repository = SqlWorkshopRepository(db_session)
    return SqlCheckInRepository(db_session, workshop_repository)


SqlCheckInRepositoryDep = Annotated[SqlCheckInRepository, Depends(get_sql_check_in_repository)]
