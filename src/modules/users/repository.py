from enum import Enum
from fastapi import HTTPException
from sqlmodel import Session, select
from typing import Sequence

from datetime import datetime, timedelta

from src.modules.workshops.schemes import WorkshopCheckin, Workshop, WorkshopCreate, WorkshopUpdate
from src.modules.users.schemes import Users

from src.modules.workshops.enums import WorkshopEnum, CheckInEnum   

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
from src.security import verify_password, get_password_hash, create_acess_token
from secrets import token_urlsafe
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.modules.users.enums import UsersEnum


class UsersRepository:
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, user_create: Users) -> tuple[Users, UsersEnum]:
        self.session.add(user_create)
        self.session.commit()
        self.session.refresh(user_create)

        return user_create, UsersEnum.CREATED
        
         
    async def read_by_email(self, user_email: str) -> Users | None:
        query = select(Users).where(Users.email == user_email)
        user = self.session.exec(query).first()
        return user
        
    