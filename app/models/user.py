from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import Relationship, SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .check_in import WorkshopCheckin  


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
    innohassle_id: str = Field(default="someid")
    hashed_password: str
    role: UserRole = Field(default=UserRole.user)
    checkins: List["WorkshopCheckin"] = Relationship(back_populates="user")



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