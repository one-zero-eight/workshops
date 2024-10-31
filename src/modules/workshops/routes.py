from fastapi import APIRouter, Response, status

from src.api.dependencies import CurrentUserIdDep
from src.api.exceptions import IncorrectCredentialsException
from src.modules.workshops.dependencies import SqlCheckInRepositoryDep, SqlWorkshopRepositoryDep
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
        status.HTTP_400_BAD_REQUEST: {"description": "Creation failed"},
    },
)
async def create_workshop(
    user_id: CurrentUserIdDep, workshop_repository: SqlWorkshopRepositoryDep, workshop: CreateWorkshopScheme
) -> ViewWorkshopScheme:
    workshop = await workshop_repository.create(workshop)
    if workshop:
        return workshop
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.post(
    "/check-in/{workshop_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Check-in successful"},
        status.HTTP_400_BAD_REQUEST: {"description": "Check-in failed"},
    },
)
async def check_in_workshop(
    workshop_id: int, user_id: CurrentUserIdDep, check_ins_repository: SqlCheckInRepositoryDep
) -> Response:
    checked_in = await check_ins_repository.create(workshop_id, user_id)
    if checked_in:
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.post(
    "/check-out/{workshop_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Check-out successful"},
        status.HTTP_400_BAD_REQUEST: {"description": "Check-out failed"},
    },
)
async def check_out_workshop(
    workshop_id: int, user_id: CurrentUserIdDep, check_ins_repository: SqlCheckInRepositoryDep
) -> Response:
    deleted = await check_ins_repository.delete(workshop_id, user_id)
    if deleted:
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.get(
    "/my-check-ins",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of workshops", "model": ViewWorkshopScheme},
    },
)
async def get_my_check_ins(
    user_id: CurrentUserIdDep, workshops_repository: SqlWorkshopRepositoryDep
) -> list[ViewWorkshopScheme]:
    return await workshops_repository.get_list_by_user_id(user_id)
