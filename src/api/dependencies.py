__all__ = ["CurrentUserDep", "current_user_dep", "AdminDep", "WorkshopRepositoryDep"]

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.exceptions import IncorrectCredentialsException
from src.config import settings
from src.logging_ import logger
from src.modules.inh_accounts_sdk import inh_accounts
from src.modules.users.repository import UsersRepository
from src.modules.users.schemas import CreateUserScheme
from src.modules.workshops.repository import WorkshopRepository
from src.storages.sql.dependencies import DbSessionDep
from src.storages.sql.models import User, UserRole

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Token from [InNoHassle Accounts](https://innohassle.ru/account/token)",
    bearerFormat="JWT",
    auto_error=False,  # We'll handle error manually
)

api_bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Secret key for accessing API by external services",
    bearerFormat="JWT",
    auto_error=False,  # We'll handle error manually
)


def get_users_repository(db_session: DbSessionDep) -> UsersRepository:
    return UsersRepository(db_session)


UsersRepositoryDep = Annotated[UsersRepository, Depends(get_users_repository)]


async def current_user_dep(
    user_repository: UsersRepositoryDep,
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    # Prefer header to cookie
    token = bearer and bearer.credentials
    if not token:
        raise IncorrectCredentialsException(no_credentials=True)
    token_data = inh_accounts.decode_token(token)
    if token_data is None:
        raise IncorrectCredentialsException(no_credentials=False)
    inh_user = await inh_accounts.get_user(innohassle_id=token_data.innohassle_id)
    assert inh_user is not None, "User not found, but token is valid. It shouldn't happen."

    if inh_user.innopolis_sso is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Connected email is required",
        )
    if inh_user.telegram is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Connected telegram is required",
        )

    user = await user_repository.fetch_or_create(
        CreateUserScheme(
            innohassle_id=token_data.innohassle_id,
            email=inh_user.innopolis_sso.email,
            telegram_username=inh_user.telegram.username,
        )
    )
    return user


CurrentUserDep = Annotated[User, Depends(current_user_dep)]
"""
Dependency for getting the current user.
"""


async def admin_dep(user: CurrentUserDep):
    if user.role != UserRole.admin:
        logger.warning("User does not have admin role.")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


AdminDep = Annotated[User, Depends(admin_dep)]
"""
Dependency for checking if the current user is an admin.
"""


async def get_workshop_repository(db_session: DbSessionDep) -> WorkshopRepository:
    return WorkshopRepository(db_session)


WorkshopRepositoryDep = Annotated[WorkshopRepository, Depends(get_workshop_repository)]


def api_key_dep(
    bearer: HTTPAuthorizationCredentials | None = Depends(api_bearer_scheme),
) -> str:
    token = bearer and bearer.credentials
    if not token:
        raise IncorrectCredentialsException(no_credentials=True)
    if token != settings.api_key.get_secret_value():
        raise IncorrectCredentialsException(no_credentials=False)
    return token


ApiKeyDep = Annotated[str, Depends(api_key_dep)]
"""
Dependency for checking if the request is coming from an authorized external service.
"""
