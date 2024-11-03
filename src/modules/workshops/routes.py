from fastapi import APIRouter, HTTPException, Response, status

from src.api.dependencies import CurrentUserIdDep
from src.api.exceptions import IncorrectCredentialsException
from src.api.schemes import ErrorScheme
from src.modules.users.schemes import ViewUserScheme
from src.modules.workshops.dependencies import SqlCheckInRepositoryDep, SqlWorkshopRepositoryDep
from src.modules.workshops.enums import CheckInEnum, WorkshopEnum
from src.modules.workshops.schemes import CreateWorkshopScheme, ViewWorkshopScheme

router = APIRouter(
    prefix="/workshops",
    tags=["Workshops"],
    responses={
        **IncorrectCredentialsException.responses,
    },
)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "All workshops"},
    },
)
async def read_all_workshops(workshop_repository: SqlWorkshopRepositoryDep) -> list[ViewWorkshopScheme]:
    return await workshop_repository.read_all()


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Workshop successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Creation failed", "model": ErrorScheme},
    },
)
async def create_workshop(
    user_id: CurrentUserIdDep, workshop_repository: SqlWorkshopRepositoryDep, workshop: CreateWorkshopScheme
) -> ViewWorkshopScheme:
    workshop, create_status = await workshop_repository.create(workshop)
    if create_status != WorkshopEnum.CREATED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=create_status.value)
    return workshop


@router.get(
    "/my-check-ins",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of workshops"},
    },
)
async def get_my_check_ins(
    user_id: CurrentUserIdDep, check_in_repository: SqlCheckInRepositoryDep
) -> list[ViewWorkshopScheme]:
    return await check_in_repository.get_check_inned_workshops_by_user_id(user_id)


@router.post(
    "/check-in/{workshop_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Check-in successful"},
        status.HTTP_400_BAD_REQUEST: {"description": "Check-in failed", "model": ErrorScheme},
    },
)
async def check_in_workshop(
    workshop_id: int, user_id: CurrentUserIdDep, check_ins_repository: SqlCheckInRepositoryDep
) -> Response:
    check_in_status = await check_ins_repository.create(workshop_id, user_id)
    if check_in_status != CheckInEnum.SUCCESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=check_in_status.value)
    return Response(status_code=status.HTTP_200_OK)


@router.post(
    "/check-out/{workshop_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Check-out successful", "model": None},
        status.HTTP_400_BAD_REQUEST: {"description": "Check-out failed", "model": ErrorScheme},
    },
)
async def check_out_workshop(
    workshop_id: int, user_id: CurrentUserIdDep, check_ins_repository: SqlCheckInRepositoryDep
) -> Response:
    delete_status = await check_ins_repository.delete(workshop_id, user_id)
    if delete_status != CheckInEnum.SUCCESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=delete_status.value)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/{workshop_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Workshop information"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop is not found"},
    },
)
async def read_workshop_by_id(workshop_repository: SqlWorkshopRepositoryDep, workshop_id: int) -> ViewWorkshopScheme:
    workshop = await workshop_repository.get_by_id(workshop_id)
    if workshop:
        return workshop
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/{workshop_id}/check-ins",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of users"},
        status.HTTP_404_NOT_FOUND: {"description": "Workshop is not found"},
    },
)
async def read_check_in_users(check_in_repository: SqlCheckInRepositoryDep, workshop_id: int) -> list[ViewUserScheme]:
    users = await check_in_repository.get_check_inned_users_by_workshop_id(workshop_id)
    if users is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return users
