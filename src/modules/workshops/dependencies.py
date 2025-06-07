
import os
from secrets import token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordBearer
from typing import List, Annotated, Sequence

from sqlmodel import Session

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# from src.api.lifespan import get_session
from src.storages.sql.dependencies import get_session
from src.modules.users.schemes import UserRole, Users
from src.modules.workshops.repository import WorkshopRepository, CheckInRepository
# from src.modules.users.schemes import Users, UserRole,
from jose import jwt, JWTError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", token_urlsafe(32))
ALGORITHM = "HS256"
TOKEN_EXPIRE_TIME = os.getenv("TOKEN_EXPIRE_TIME", 60)


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]

async def get_workshop_repository(db_session: DbSessionDep) -> WorkshopRepository:
    return WorkshopRepository(db_session)

WorkshopRepositoryDep = Annotated[WorkshopRepository, Depends(get_workshop_repository)]

async def get_checkin_repository(db_session: DbSessionDep, workshop_repo: WorkshopRepositoryDep) -> CheckInRepository:
    return CheckInRepository(db_session, workshop_repo)

CheckInRepositoryDep = Annotated[CheckInRepository, Depends(get_checkin_repository)]


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub", "0")
        user = await session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

UserDep = Annotated[Users, Depends(get_current_user)]

async def is_admin(user: UserDep):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

AdminDep = Annotated[Users, Depends(is_admin)]
