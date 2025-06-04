from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, update
from typing import List
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

from app.crud.config import get_session
import models
from app.security import verify_password, get_password_hash
from secrets import token_urlsafe

load_dotenv()

router = APIRouter(prefix="/users")

SECRET_KEY = os.getenv("SECRET_KEY", token_urlsafe(32))
ALGORITHM = "HS256"


@router.post("/login")
async def login(user_login: models.UserLogin, session: Session = Depends(get_session)):
    user = select(models.User)
    user = session.exec(user.where(
        models.User.email == user_login.email)).first()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid email or password")

    token_data = {"sub": user.id, "role": user.role}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register")
async def register(user_create: models.UserCreate, session: Session = Depends(get_session)):
    hashed_pwd = get_password_hash(user_create.password)
    user = models.User.model_validate(
        user_create, update={"hashed_password": hashed_pwd})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
