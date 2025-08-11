from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import CurrentUserDep, UsersRepositoryDep, WorkshopRepositoryDep
from src.config import settings
from src.storages.sql.models import User, UserRole, Workshop

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", responses={200: {"description": "Current user info"}})
async def get_me(user: CurrentUserDep) -> User:
    """
    Get current user info if authenticated
    """
    return user


@router.get(
    "/my_checkins",
    responses={
        status.HTTP_200_OK: {"description": "User's check-ins retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
    },
)
async def get_my_checkins(
    workshop_repo: WorkshopRepositoryDep,
    user: CurrentUserDep,
) -> list[Workshop]:
    workshops = await workshop_repo.get_checked_in_workshops(user.innohassle_id)
    return list(workshops)


@router.post(
    "/change_role",
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
    user_to_change_email: str,
) -> User:
    """
    Change role of user by email
    """
    if current_user.email not in settings.superadmin_emails:
        raise HTTPException(status_code=403, detail="Only superadmin can change role")
    user_to_change = await users_repo.read_by_email(user_to_change_email)
    if not user_to_change:
        raise HTTPException(status_code=404, detail="User to change not found")
    await users_repo.change_role_of_user(user_to_change, role)
    return user_to_change
