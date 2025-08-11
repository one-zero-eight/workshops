from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    AdminDep,
    CurrentUserDep,
    WorkshopRepositoryDep,
)
from src.logging_ import logger
from src.modules.users.schemas import ViewUserScheme
from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.storages.sql.models import CreateWorkshop, UpdateWorkshop, UserRole, Workshop

router = APIRouter(prefix="/workshops", tags=["Workshops"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Workshop successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Workshop creation failed"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
    },
)
async def add_workshop(
    workshop_repo: WorkshopRepositoryDep,
    workshop_create: CreateWorkshop,
    _: AdminDep,
) -> Workshop:
    """
    Add a new workshop
    """
    workshop, status = await workshop_repo.create(workshop_create)
    if status != WorkshopEnum.CREATED:
        raise HTTPException(status_code=400, detail=status.value)
    if not workshop:
        raise HTTPException(status_code=400, detail="Workshop creation failed")
    return workshop


@router.get(
    "/",
    responses={
        status.HTTP_200_OK: {"description": "All workshops retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
    },
)
async def get_all_workshops(
    workshop_repo: WorkshopRepositoryDep,
    limit: int = 100,
) -> list[Workshop]:
    workshops = await workshop_repo.get_all(limit)
    return list(workshops)


@router.put(
    "/{workshop_id}",
    responses={
        status.HTTP_200_OK: {"description": "Workshop updated successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
    },
)
async def update_workshop(
    workshop_id: str,
    workshop: UpdateWorkshop,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
) -> Workshop:
    updatedWorkshop, status = await workshop_repo.update(workshop_id, workshop)
    if not updatedWorkshop:
        raise HTTPException(status_code=404, detail=status.value)
    if status != WorkshopEnum.UPDATED:
        raise HTTPException(status_code=400, detail=status.value)
    return updatedWorkshop


@router.post(
    "/{workshop_id}/activate",
    responses={
        status.HTTP_200_OK: {"description": "Workshop activated"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
    },
)
async def activate_workshop(
    workshop_id: str,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
) -> Workshop:
    workshop = await workshop_repo.set_active(workshop_id, True)
    if not workshop:
        raise HTTPException(status_code=404, detail=WorkshopEnum.WORKSHOP_DOES_NOT_EXIST.value)
    return workshop


@router.post(
    "/{workshop_id}/deactivate",
    responses={
        status.HTTP_200_OK: {"description": "Workshop deactivated"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
    },
)
async def deactivate_workshop(
    workshop_id: str,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
) -> Workshop:
    workshop = await workshop_repo.set_active(workshop_id, False)
    if not workshop:
        logger.error("Failed during deactivating workshop.")
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop


@router.delete(
    "/{workshop_id}",
    responses={
        status.HTTP_200_OK: {"description": "Workshop deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
    },
)
async def delete_workshop(
    workshop_id: str,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
):
    status = await workshop_repo.delete(workshop_id)
    if status != WorkshopEnum.DELETED:
        logger.error(f"Failed during deleting workshop. Status: {status}")
        raise HTTPException(status_code=404, detail=status.value)

    return {"message": WorkshopEnum.DELETED.value}


@router.post(
    "/{workshop_id}/checkin",
    responses={
        status.HTTP_200_OK: {"description": "User successfully checked in"},
        status.HTTP_400_BAD_REQUEST: {"description": "Some error occurred during checkin"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
    },
)
async def checkin_user(
    workshop_id: str,
    user: CurrentUserDep,
    workshop_repo: WorkshopRepositoryDep,
) -> None:
    """
    Check in a user to a workshop
    """
    check_in_status = await workshop_repo.check_in(user.innohassle_id, workshop_id)
    if check_in_status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST:
        raise HTTPException(status_code=404, detail=check_in_status.value)
    elif check_in_status != CheckInEnum.SUCCESS:
        raise HTTPException(status_code=400, detail=check_in_status.value)
    return None


@router.post(
    "/{workshop_id}/checkout",
    responses={
        status.HTTP_200_OK: {"description": "User successfully checked out"},
        status.HTTP_400_BAD_REQUEST: {"description": "Some error occurred during checkout"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
    },
)
async def checkout_user(
    workshop_id: str,
    workshop_repo: WorkshopRepositoryDep,
    user: CurrentUserDep,
):
    remove_check_in_status = await workshop_repo.check_out(user.innohassle_id, workshop_id)
    if remove_check_in_status == CheckInEnum.WORKSHOP_DOES_NOT_EXIST:
        raise HTTPException(status_code=404, detail=remove_check_in_status.value)
    elif remove_check_in_status != CheckInEnum.SUCCESS:
        raise HTTPException(status_code=400, detail=remove_check_in_status.value)
    return None


@router.get(
    "/{workshop_id}/checkins",
    responses={
        status.HTTP_200_OK: {"description": "All check-ins retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
    },
)
async def get_all_check_ins(
    workshop_id: str,
    workshop_repo: WorkshopRepositoryDep,
    user: CurrentUserDep,
) -> list[ViewUserScheme]:
    workshop = await workshop_repo.get(workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    users = await workshop_repo.get_checked_in_users(workshop_id)
    validated = [ViewUserScheme.model_validate(user) for user in users]
    if user.role != UserRole.admin:
        for u in validated:
            u.telegram_username = None  # set to None for non-admins to avoid leaking info
    return validated
