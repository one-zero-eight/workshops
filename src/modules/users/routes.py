from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, update
from typing import Annotated, List
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

from src.api.lifespan import get_session
from src.modules.users.schemes import Users, UserCreate
from src.modules.tokens.schemes import Token
from src.modules.workshops.dependencies import CheckInRepositoryDep, UserDep
from src.modules.workshops.schemes import WorkshopReadAll
from src.security import verify_password, get_password_hash, create_acess_token
from secrets import token_urlsafe
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.modules.users.enums import UsersEnum
from src.modules.users.dependencies import UsersRepositoryDep

load_dotenv()

router = APIRouter(prefix="/users")

SECRET_KEY = os.getenv("SECRET_KEY", token_urlsafe(32))
ALGORITHM = "HS256"

#TODO: Remove typo here
TOKEN_EXPIRE_TIME = os.getenv("TOKEN_EXPIRE_TIME1", 60)


@router.post("/register",
             status_code=status.HTTP_201_CREATED,
             response_model=Token,
             responses= {status.HTTP_400_BAD_REQUEST: {"description": "Email already registered"}})
async def register(user_create: UserCreate,
                   session: Annotated[Session, Depends(get_session)],
                   users_repo: UsersRepositoryDep):
    hashed_pwd = get_password_hash(user_create.password)
    user = Users.model_validate(
        user_create, update={"hashed_password": hashed_pwd})
    
    
    user_read = await users_repo.read_by_email(user.email)
    
    if user_read is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    #TODO: Check for bugs
    user_created, response_value = await users_repo.create(user)  # type: ignore
    if response_value != UsersEnum.CREATED:
        raise HTTPException(status_code=400, detail="User could not be created")
    
    access_token = create_acess_token(
        str(user_created.id), timedelta(minutes=int(TOKEN_EXPIRE_TIME)))
    return Token(access_token=access_token)


@router.post("/login/access-token",
             status_code=status.HTTP_200_OK, 
             response_model=Token, 
             responses={status.HTTP_401_UNAUTHORIZED: {"description": "Invalid email or password"}})
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                users_repo: UsersRepositoryDep,
                session: Annotated[Session, Depends(get_session)]):

    user = await users_repo.read_by_email(form_data.username)

    #TODO: Replace all checks to separated class IncorrectCredentialsException

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid email or password")

    token = create_acess_token(
        str(user.id), timedelta(minutes=int(TOKEN_EXPIRE_TIME)))
    return Token(access_token=token)


@router.get("/my_checkins",
            response_model=List[WorkshopReadAll],
            responses={
                status.HTTP_200_OK: {"description": "User's check-ins retrieved successfully"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
            })
async def get_my_checkins(
    user: UserDep,
    checkin_repo: CheckInRepositoryDep,
):
    workshops = await checkin_repo.get_checked_in_workshops_for_user(user.id)
    if not workshops:
        raise HTTPException(status_code=404, detail="No check-ins found for this user")
    return [WorkshopReadAll.model_validate(workshop) for workshop in workshops]
    