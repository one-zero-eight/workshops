__all__ = ["CurrentUserIdDep", "get_current_user_id"]

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.exceptions import IncorrectCredentialsException
from src.modules.tokens.dependencies import TokenRepositoryDep

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Token from [InNoHassle Accounts](https://api.innohassle.ru/accounts/v0/tokens/generate-my-token)",
    bearerFormat="JWT",
    auto_error=True,  # We'll handle error manually
)


async def get_current_user_id(
    token_repository: TokenRepositoryDep, bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> str:
    # Prefer header to cookie
    token = bearer and bearer.credentials
    if not token:
        raise IncorrectCredentialsException(no_credentials=True)
    token_data = await token_repository.verify_user_token(token, IncorrectCredentialsException())
    return token_data.user_id

CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]
