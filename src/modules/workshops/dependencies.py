
from fastapi import Depends, HTTPException, status
from typing import Annotated


from src.api.dependencies import CurrentUserIdDep
from src.modules.users.dependencies import UsersRepositoryDep
from src.storages.sql.dependencies import DbSessionDep
from src.modules.users.schemes import UserRole
from src.storages.sql.models.users import User

from src.modules.workshops.repository import WorkshopRepository, CheckInRepository
from src.logging import logger

async def get_workshop_repository(db_session: DbSessionDep) -> WorkshopRepository:
    return WorkshopRepository(db_session)

WorkshopRepositoryDep = Annotated[WorkshopRepository, Depends(
    get_workshop_repository)]


async def get_checkin_repository(db_session: DbSessionDep, workshop_repo: WorkshopRepositoryDep) -> CheckInRepository:
    return CheckInRepository(db_session, workshop_repo)

CheckInRepositoryDep = Annotated[CheckInRepository, Depends(
    get_checkin_repository)]


async def is_admin(user_id: CurrentUserIdDep, user_repo: UsersRepositoryDep):
    user = await user_repo.read_by_id(user_id)  # type: ignore
    if user is None:
        logger.warning("User not found.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User does not exists")

    if user.role != UserRole.admin:
        logger.warning("User does not have admin role.")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

AdminDep = Annotated[User, Depends(is_admin)]
