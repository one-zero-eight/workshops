from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, update
from typing import Annotated, List
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

from app.crud.config import get_session
from app.models.check_in import WorkshopCheckin
from app.models.user import Users, UserRole, UserCreate, UserRead, UserLogin, Token
from app.models.workshop import Workshop
from app.security import verify_password, get_password_hash, create_acess_token
from secrets import token_urlsafe
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


load_dotenv()

router = APIRouter(prefix="/users")

SECRET_KEY = os.getenv("SECRET_KEY", token_urlsafe(32))
ALGORITHM = "HS256"
TOKEN_EXPIRE_TIME = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub", "0")
        user = session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDkwMzYxMjcsInN1YiI6ImI1OGQ5MzM3LWFmYzUtNGJiNy1hMmQ3LWE0YjA0NmNkZmY1MCJ9.SO6JrZazdBVpSHsAxBDn-sls0_WReoRDRN-pDUR6IwQ


def is_admin(user: Annotated[Users, Depends(get_current_user)]):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/register", response_model=Token)
async def register(user_create: UserCreate, session: Annotated[Session, Depends(get_session)]):
    exists = session.exec(select(Users).where(
        Users.email == user_create.email)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = get_password_hash(user_create.password)
    user = Users.model_validate(
        user_create, update={"hashed_password": hashed_pwd})
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token = create_acess_token(
        str(user.id), timedelta(minutes=TOKEN_EXPIRE_TIME))
    return Token(access_token=access_token)


@router.post("/login/access-token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Annotated[Session, Depends(get_session)]):
    user = select(Users)
    user = session.exec(user.where(
        Users.email == form_data.username)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid email or password")

    token = create_acess_token(
        str(user.id), timedelta(minutes=TOKEN_EXPIRE_TIME))
    return Token(access_token=token)
