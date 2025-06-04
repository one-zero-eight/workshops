from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import Optional


def generate_uuid_id():
    return str(uuid.uuid4())


class UserRole(str, Enum):
    admin = "admin"
    user = "user"

# class BaseUser(SQLModel):
#     full_name: str = Field(max_length=255)
#     email: str = Field()
#     role: UserRole = Field(default=UserRole.user)


class Users(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid_id, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.user)

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDkwMzQzNzYsInN1YiI6ImE5NTU5MDZjLWY4MzktNDQwYi04MmI3LWIwNDIyYjI3ZDZmMyJ9.BGXJz02CbVnv3ahF8GLdddWCcN7H5-UdsEBX41B0FCA


class UserCreate(SQLModel):
    email: str
    password: str


class UserLogin(SQLModel):
    email: str
    password: str


class UserRead(SQLModel):
    id: str
    name: str
    email: str
    role: UserRole


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
