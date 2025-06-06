from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import Relationship, SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import TYPE_CHECKING, List, Optional
from src.utils.utils import generate_uuid_id

#TODO: Add Alembic migrations

if TYPE_CHECKING:
    from src.modules.workshops.schemes import WorkshopCheckin


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class Users(SQLModel, table=True):
    __tablename__: str = "users" # type: ignore
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
    email: str
    role: UserRole


