from fastapi import APIRouter, HTTPException, Response, status
from typing import List


from src.modules.workshops.enums import WorkshopEnum, CheckInEnum
from src.modules.users.schemes import ViewUserScheme
from src.api.dependencies import CurrentUserIdDep
from src.modules.workshops.schemes import ReadWorkshopScheme, CreateWorkshopScheme, UpdateWorkshopScheme

from src.modules.workshops.dependencies import WorkshopRepositoryDep, CheckInRepositoryDep, AdminDep

from src.modules.users.dependencies import UsersRepositoryDep
from src.logging import logger

router = APIRouter(prefix="/api/workshops")


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=ReadWorkshopScheme,
             responses={
                 status.HTTP_201_CREATED: {"description": "Workshop successfully created"},
                 status.HTTP_400_BAD_REQUEST: {"description": "Workshop creation failed"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
             })
async def add_workshop(*,
                       workshop_repo: WorkshopRepositoryDep,
                       workshop_create: CreateWorkshopScheme,
                       _: AdminDep,):
    workshop, status = await workshop_repo.create_workshop(workshop_create)
    if status != WorkshopEnum.CREATED:
        logger.error(f"Failed during adding workshop. Status: {status}")
        raise HTTPException(status_code=400, detail=status.value)
    return ReadWorkshopScheme.model_validate(workshop)


@router.get("/",
            response_model=List[ReadWorkshopScheme],
            responses={
                status.HTTP_200_OK: {"description": "All workshops retrieved successfully"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
            })
async def get_all_workshops(
    *,
    workshop_repo: WorkshopRepositoryDep,
    limit: int = 100,
    _: CurrentUserIdDep,
):
    workshops = await workshop_repo.get_all_workshops(limit)
    return [ReadWorkshopScheme.model_validate(workshop) for workshop in workshops]

#TODO: Add enums for updates
@router.put("/{workshop_id}",
            responses={
                status.HTTP_200_OK: {"description": "Workshop updated successfully"},
                status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
            })
async def update_workshop(
    workshop_id: str,
    workshop: UpdateWorkshopScheme,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
):
    updatedWorkshop = await workshop_repo.update_workshop(workshop_id, workshop)
    if not updatedWorkshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    return {"message": "Workshop updated successfully"}


@router.post("/{workshop_id}/activate",
             responses={
                 status.HTTP_200_OK: {"description": "Workshop activated"},
                 status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
             })
async def activate_workshop(
    workshop_id: str,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
):
    workshop = await workshop_repo.change_active_status_workshop(workshop_id, True)
    if not workshop:
        logger.error(f"Failed during activating workshop.")
        raise HTTPException(status_code=404, detail="Workshop not found")
    return Response(status_code=status.HTTP_200_OK)


@router.post("/{workshop_id}/deactivate",
             responses={
                 status.HTTP_200_OK: {"description": "Workshop deactivated"},
                 status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
             })
async def deactivate_workshop(
    workshop_id: str,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
):
    workshop = await workshop_repo.change_active_status_workshop(workshop_id, False)
    if not workshop:
        logger.error(f"Failed during deactivating workshop.")
        raise HTTPException(status_code=404, detail="Workshop not found")
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/{workshop_id}",
               responses={
                   status.HTTP_200_OK: {"description": "Workshop deleted successfully"},
                   status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                   status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                   status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
               })
async def delete_workshop(workshop_id: str,
                          _: AdminDep,
                          workshop_repo: WorkshopRepositoryDep,
                          ):
    status = await workshop_repo.delete_workshop(workshop_id)
    if status != WorkshopEnum.DELETED:
        logger.error(f"Failed during deleting workshop. Status: {status}")
        raise HTTPException(status_code=404, detail="Workshop not found")

    return {"message": "Workshop deleted successfully"}


@router.post("/{workshop_id}/checkin",
             responses={
                 status.HTTP_200_OK: {"description": "User successfully checked in"},
                 status.HTTP_404_NOT_FOUND: {"description": "Workshop not found or other check-in error"},
                 status.HTTP_400_BAD_REQUEST: {"description": "Check-in conditions not met"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
             })
async def checkin_user(
    workshop_id: str,
    user_id: CurrentUserIdDep,
    checkin_repo: CheckInRepositoryDep,
    user_repo: UsersRepositoryDep
):
    user = await user_repo.read_by_id(user_id)  # type: ignore
    if user is None:
        raise HTTPException(
            status_code=500, detail="User not found")

    check_in_status = await checkin_repo.create_checkIn(user.id, workshop_id)

    if check_in_status != CheckInEnum.SUCCESS:
        logger.error(f"Failed during checking in user. Status: {status}")
        raise HTTPException(status_code=404, detail=check_in_status.value)

    return Response(status_code=status.HTTP_200_OK)


@router.post("/{workshop_id}/checkout",
             responses={
                 status.HTTP_200_OK: {"description": "User successfully checked out"},
                 status.HTTP_404_NOT_FOUND: {"description": "Check-in not found or workshop missing"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
             })
async def checkout_user(
    workshop_id: str,
    checkin_repo: CheckInRepositoryDep,
    user_id: CurrentUserIdDep,
    user_repo: UsersRepositoryDep
):
    user = await user_repo.read_by_id(user_id)  # type: ignore
    if user is None:
        raise HTTPException(
            status_code=500, detail="User not found")

    remove_check_in_status = await checkin_repo.remove_checkIn(user.id, workshop_id)
    if remove_check_in_status != CheckInEnum.SUCCESS:
        raise HTTPException(
            status_code=404, detail=remove_check_in_status.value)

    return Response(status_code=status.HTTP_200_OK)


@router.get("/{workshop_id}/checkins")
async def get_all_check_ins(
    workshop_id: str,
    user: AdminDep,
    checkin_repo: CheckInRepositoryDep,
):
    users = await checkin_repo.get_checked_in_users_for_workshop(workshop_id)
    if not users:
        logger.error(f"Failed during checking in user. Status: {status}")
        raise HTTPException(
            status_code=404, detail="No check-ins found for this workshop")

    return [ViewUserScheme.model_validate(user) for user in users]
