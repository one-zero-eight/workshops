from typing import Annotated

from fastapi import Depends

from src.modules.tokens.repository import TokenRepository
from src.modules.users.dependencies import UsersRepositoryDep


async def get_tokens_repository(user_repository: UsersRepositoryDep) -> TokenRepository:
    return TokenRepository(user_repository)


TokenRepositoryDep = Annotated[TokenRepository, Depends(get_tokens_repository)]
