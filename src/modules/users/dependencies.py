from typing import Annotated
from fastapi import Depends
from src.modules.workshops.dependencies import DbSessionDep
from src.modules.users.repository import UsersRepository

def get_users_repository(db_session: DbSessionDep) -> UsersRepository:
    return UsersRepository(db_session)

UsersRepositoryDep = Annotated[UsersRepository, Depends(get_users_repository)]
