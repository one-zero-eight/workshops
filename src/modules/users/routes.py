from fastapi import APIRouter

from src.api.dependencies import CurrentUserIdDep
from src.api.exceptions import IncorrectCredentialsException
from src.modules.users.dependencies import SqlUserRepositoryDep
from src.modules.users.schemes import ViewUserScheme

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        **IncorrectCredentialsException.responses,
    },
)


@router.get("/me", responses={200: {"description": "Current user info"}})
async def get_me(user_id: CurrentUserIdDep, user_repository: SqlUserRepositoryDep) -> ViewUserScheme:
    """
    Get current user info if authenticated
    """
    user = await user_repository.read(user_id)
    return user
