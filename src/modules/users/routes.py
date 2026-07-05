from fastapi import APIRouter, HTTPException, Path, status

from src.api.dependencies import ApiKeyDep, CurrentUserDep, EventRepositoryDep, UsersRepositoryDep
from src.config import settings
from src.storages.sql.models import Event, User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", responses={200: {"description": "Current user info"}})
async def get_me(user: CurrentUserDep) -> User:
    """
    Get current user info if authenticated
    """
    return user


@router.get(
    "/me/registrations",
    responses={
        status.HTTP_200_OK: {"description": "User's registrations retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
    },
)
async def get_my_registrations(
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> list[Event]:
    events = await event_repo.get_registered_events(user.innohassle_id)
    return list(events)


@router.patch(
    "/{user_id}/role",
    responses={
        status.HTTP_200_OK: {"description": "Changed role succesfully, returns updated user"},
        status.HTTP_403_FORBIDDEN: {"description": "Only superadmin can change role"},
        status.HTTP_404_NOT_FOUND: {"description": "User to change not found"},
    },
)
async def change_role(
    role: UserRole,
    users_repo: UsersRepositoryDep,
    current_user: CurrentUserDep,
    user_id: str = Path(..., description="InNoHassle ID of the user to change"),
) -> User:
    """
    Change role of user by ID
    """
    if current_user.email not in settings.superadmin_emails:
        raise HTTPException(status_code=403, detail="Only superadmin can change role")
    user_to_change = await users_repo.read_by_innohassle_id(user_id)
    if not user_to_change:
        raise HTTPException(status_code=404, detail="User to change not found")
    await users_repo.change_role_of_user(user_to_change, role)
    return user_to_change


@router.get(
    "/{user_id}/registrations",
    responses={
        status.HTTP_200_OK: {"description": "User's registrations retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
async def get_user_registrations(
    user_id: str,
    user_repo: UsersRepositoryDep,
    event_repo: EventRepositoryDep,
    _api_dep: ApiKeyDep,
) -> list[Event]:
    user = await user_repo.read_by_innohassle_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    events = await event_repo.get_registered_events(user_id)
    return list(events)
