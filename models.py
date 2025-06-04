from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import Optional


def generate_uuid_id():
    return str(uuid.uuid4())


class BaseWorkshop(SQLModel):
    title: str = Field(index=True, max_length=255)
    workshop_start_time: datetime = Field()
    duration: timedelta = Field()
    place: Optional[str] = Field(default=None)
    available_places: int = Field(
        default=10, ge=0, description="Number of available places left")
    max_places: int = Field(
        default=10, ge=0,  description="Maximum number of places available")


class Workshop(BaseWorkshop, table=True):
    id: str = Field(
        default_factory=generate_uuid_id,
        primary_key=True,
        index=True
    )
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkshopCreate(BaseWorkshop):
    pass


class WorkshopRead(BaseWorkshop):
    id: str
    created_at: datetime
    description: Optional[str]


class WorkshopUpdate(SQLModel):
    title: Optional[str] = None
    workshop_start_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    place: Optional[str] = None
    available_places: Optional[int] = None
    max_places: Optional[int] = None


class UserRole(str, Enum):
    admin = "admin"
    user = "user" 

class BaseUser(SQLModel):
    full_name: str = Field(max_length=255)
    email: str = Field()
    role: UserRole = Field(default=UserRole.user)

class User(BaseUser, table=True):
    id: str = Field(default_factory=generate_uuid_id, primary_key=True)
    hashed_password: str = Field(max_length=40)

class UserCreate(SQLModel):
    full_name: str
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