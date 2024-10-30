from fastapi import APIRouter, Response, status

from src.api.dependencies.auth import CurrentUserIdDep
from src.api.exceptions import IncorrectCredentialsException
from src.modules.workshops.dependencies import SqlCheckInRepositoryDep, SqlWorkshopRepositoryDep
from src.modules.workshops.schemes import ViewWorkshopScheme

router = APIRouter(
    prefix="/workshops",
    tags=["Workshops"],
    responses={
        **IncorrectCredentialsException.responses,
    },
)


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
