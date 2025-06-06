import os
from secrets import token_urlsafe
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from typing import List



from src.modules.workshops.enums import WorkshopEnum, CheckInEnum
from src.modules.workshops.schemes import WorkshopCreate, WorkshopRead, WorkshopReadAll, WorkshopUpdate
from src.modules.users.schemes import UserRead


from src.modules.workshops.dependencies import WorkshopRepositoryDep, DbSessionDep, CheckInRepositoryDep, AdminDep, UserDep

router = APIRouter(prefix="/api/workshops")

# TODO: Cancel out all dependencies here

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", token_urlsafe(32))
ALGORITHM = "HS256"
TOKEN_EXPIRE_TIME = os.getenv("TOKEN_EXPIRE_TIME", 60)




# def get_workshop_or_404(session: Session, workshop_id: str) -> Workshop:
#     workshop = session.get(Workshop, workshop_id)
#     if not workshop:
#         raise HTTPException(status_code=404, detail="Workshop not found")
#     return workshop


# def get_workshops_for_user(session: Session, user_id: str) -> Sequence[Workshop]:
#     statement = select(Workshop).join(WorkshopCheckin).where(
#         WorkshopCheckin.user_id == user_id)

#     results = session.exec(statement)
#     return results.all()


# def validate_checkin_conditions(session: Session, user: Users, workshop: Workshop):
#     if not workshop.is_active:
#         raise HTTPException(
#             status_code=400, detail="This workshop is not active")
#     if workshop.remain_places <= 0:
#         raise HTTPException(
#             status_code=400, detail="No available places left in this workshop.")
#     if workshop.dtstart >= datetime.now() + timedelta(days=1):
#         raise HTTPException(
#             status_code=400, detail="This workshop will start in more than 1 day")

#     checked_in_workshops = get_workshops_for_user(session, user.id)
#     for other in checked_in_workshops:
#         if other.dtstart <= workshop.dtend and workshop.dtstart <= other.dtend:
#             raise HTTPException(
#                 status_code=400, detail="This workshop overlaps with another you're already checked in to.")

@router.post("/",
             status_code=status.HTTP_201_CREATED,
             response_model=WorkshopRead,
             responses={
                 status.HTTP_201_CREATED: {"description": "Workshop successfully created"},
                 status.HTTP_400_BAD_REQUEST: {"description": "Workshop creation failed"},
                 status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                 status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
             })
async def add_workshop(*,
                       session: DbSessionDep,
                       workshop_repo: WorkshopRepositoryDep,
                       workshop_create: WorkshopCreate,
                       _: AdminDep):
    workshop, status = await workshop_repo.create_workshop(workshop_create)
    if status != WorkshopEnum.CREATED:
        raise HTTPException(status_code=400, detail=status.value)
    return WorkshopRead.model_validate(workshop)


@router.get("/{workshop_id}",
            response_model=WorkshopRead,
            responses={
                status.HTTP_200_OK: {"description": "Workshop details"},
                status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
            })
async def get_workshop_details(
    *,
    session: DbSessionDep,
    workshop_repo: WorkshopRepositoryDep,
    workshop_id: str,
    _: UserDep
):
    workshop = await workshop_repo.get_workshop_by_id(workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return WorkshopRead.model_validate(workshop)


@router.get("/",
            response_model=List[WorkshopReadAll],
            responses={
                status.HTTP_200_OK: {"description": "All workshops retrieved successfully"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
            })
async def get_all_workshops(
    *,
    workshop_repo: WorkshopRepositoryDep,
    limit: int = 100,
    _: UserDep
):
    workshops = await workshop_repo.get_all_workshops(limit)
    # if not workshops:
    #     raise HTTPException(status_code=404, detail="No workshops found")
    return [WorkshopReadAll.model_validate(workshop) for workshop in workshops]

#TODO: Write my checkins for user and all users for admin

@router.put("/{workshop_id}",
            responses={
                status.HTTP_200_OK: {"description": "Workshop updated successfully"},
                status.HTTP_404_NOT_FOUND: {"description": "Workshop not found"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
                status.HTTP_403_FORBIDDEN: {"description": "Not authorized (admin required)"},
            })
async def update_workshop(
    workshop_id: str,
    workshop: WorkshopUpdate,
    _: AdminDep,
    workshop_repo: WorkshopRepositoryDep,
):
    workshops = await workshop_repo.update_workshop(workshop_id, workshop)
    if not workshops:
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
    session: DbSessionDep
):
    workshop = await workshop_repo.change_active_status_workshop(workshop_id, True)
    if not workshop:
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
    session: DbSessionDep
):
    workshop = await workshop_repo.change_active_status_workshop(workshop_id, False)
    if not workshop:
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
                          session: DbSessionDep
                          ):
    workshops = await workshop_repo.delete_workshop(workshop_id)
    if workshops != WorkshopEnum.DELETED:
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
    user: UserDep,
    checkin_repo: CheckInRepositoryDep,
):
    check_in_status = await checkin_repo.create_checkIn(user.id, workshop_id)

    if check_in_status != CheckInEnum.SUCCESS:
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
    user: UserDep,
    checkin_repo: CheckInRepositoryDep,
):
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
        raise HTTPException(status_code=404, detail="No check-ins found for this workshop")

    return [UserRead.model_validate(user) for user in users]    

    
    