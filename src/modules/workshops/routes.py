import asyncio

import magic
import pyvips
from fastapi import APIRouter, HTTPException, UploadFile, status
from starlette.responses import RedirectResponse

import src.modules.workshops.minio as minio
from src.api.dependencies import (
    CurrentUserDep,
    WorkshopRepositoryDep,
)
from src.logging_ import logger
from src.modules.clubs.dependencies import UserClubsDep
from src.modules.inh_accounts_sdk import inh_accounts
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
    user: CurrentUserDep,
    user_clubs: UserClubsDep,
) -> Workshop:
    """
    Add a new workshop
    """
    if (
        not any([user_club.title == workshop_create.host for user_club in user_clubs])
        and not user.role == UserRole.admin
    ):
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can add workshops with other clubs as hosts. You can create "
            f"workshops with following clubs as host: {[user_club.title for user_club in user_clubs]}",
        )

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
    },
)
async def get_all_workshops(
    workshop_repo: WorkshopRepositoryDep,
    limit: int = 100,
) -> list[Workshop]:
    workshops = await workshop_repo.get_all(limit)
    return list(workshops)


@router.get(
    "/{workshop_id}",
    responses={
        status.HTTP_200_OK: {"description": "Workshop retrieved successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
    },
)
async def get_workshop(
    workshop_id: str,
    workshop_repo: WorkshopRepositoryDep,
) -> Workshop | None:
    workshop = await workshop_repo.get(workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop


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
    workshop_repo: WorkshopRepositoryDep,
    user: CurrentUserDep,
    user_clubs: UserClubsDep,
) -> Workshop:
    update_workshop = await workshop_repo.get(workshop_id)
    if not update_workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    if (
        not any([user_club.title == update_workshop.host for user_club in user_clubs])
        and not user.role == UserRole.admin
    ):
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can edit workshops with other clubs as hosts. You can edit "
            f"workshops with following clubs as host: {[user_club.title for user_club in user_clubs]}",
        )

    updated_workshop, status = await workshop_repo.update(workshop_id, workshop)
    if not updated_workshop:
        raise HTTPException(status_code=404, detail=status.value)
    if status != WorkshopEnum.UPDATED:
        raise HTTPException(status_code=400, detail=status.value)
    return updated_workshop


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
    user: CurrentUserDep,
    user_clubs: UserClubsDep,
    workshop_repo: WorkshopRepositoryDep,
):
    delete_workshop = await workshop_repo.get(workshop_id)
    if not delete_workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    if (
        not any([user_club.title == update_workshop.host for user_club in user_clubs])
        and not user.role == UserRole.admin
    ):
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can delete workshops with other clubs as hosts. You can delete "
            f"workshops with following clubs as host: {[user_club.title for user_club in user_clubs]}",
        )

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
            u.name = None
    else:
        user_info_tasks = [inh_accounts.get_user(email=u.email) for u in validated]
        user_infos = await asyncio.gather(*user_info_tasks, return_exceptions=True)

        for u, user_info in zip(validated, user_infos):
            if isinstance(user_info, BaseException):
                continue
            if user_info and user_info.innopolis_sso:
                u.name = user_info.innopolis_sso.name
    return validated


@router.get(
    "/{workshop_id}/image",
    responses={
        status.HTTP_307_TEMPORARY_REDIRECT: {"description": "Redirect to the event image"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found or no logo available"},
    },
    response_model=None,
)
async def get_event_image(
    workshop_id: str,
    workshop_repo: WorkshopRepositoryDep,
):
    workshop = await workshop_repo.get(workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    if not workshop.image_file_id:
        raise HTTPException(status_code=404, detail="No image available")

    return RedirectResponse(url=minio.get_event_picture_url(workshop.image_file_id))


@router.post(
    "/{workshop_id}/image",
    responses={
        status.HTTP_200_OK: {"description": "Changed event image successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid content type"},
        status.HTTP_403_FORBIDDEN: {"description": "Only admin can change event image"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def set_event_image(
    workshop_id: str,
    image_file: UploadFile,
    workshop_repo: WorkshopRepositoryDep,
    user: CurrentUserDep,
    user_clubs: UserClubsDep,
) -> Workshop:
    workshop = await workshop_repo.get(workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    if not any([user_club.title == workshop.host for user_club in user_clubs]) and not user.role == UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can edit workshops with other clubs as hosts. You can edit "
            f"workshops with following clubs as host: {[user_club.title for user_club in user_clubs]}",
        )

    bytes_ = await image_file.read()
    content_type = image_file.content_type
    if content_type is None:
        content_type = magic.Magic(mime=True).from_buffer(bytes_)

    supported_content_types = ["image/jpeg", "image/png", "image/webp"]
    if content_type not in supported_content_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid content type ({content_type}), must be one of {supported_content_types}"
        )

    # Convert to webp
    image: pyvips.Image = pyvips.Image.new_from_buffer(bytes_, "")
    image_bytes = image.write_to_buffer(".webp")

    # Save file
    image_file_id = workshop_id
    minio.put_event_picture(image_file_id, image_bytes, "image/webp")
    await workshop_repo.update_image_file_id(workshop_id, image_file_id)
    return workshop
