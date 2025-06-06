from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import Relationship, SQLModel, create_engine, Session, Field
from datetime import timedelta

from pydantic import model_validator

from typing import TYPE_CHECKING, List, Optional
# from app.models.check_in import WorkshopCheckin
# from app.models.check_in import WorkshopCheckin
from src.modules.users.schemes import Users
from src.utils.utils import generate_uuid_id


class BaseWorkshop(SQLModel):
    name: str = Field(index=True, max_length=255)
    alias: str = Field(max_length=255, unique=True)
    # description: Optional[str] = Field(default=None)
    dtstart: datetime
    # workshop_start_time: datetime = Field()
    dtend: datetime
    place: Optional[str] = Field(default=None)
    capacity: int = Field(ge=0)
    remain_places: int = Field(default=10, ge=0)
    is_active: Optional[bool] = False
    
    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self

    @model_validator(mode="after")
    def validate_capacity(self):
        if self.remain_places > self.capacity:
            raise ValueError("`remain_places` cannot be greater than `capacity`")
        return self

class Workshop(BaseWorkshop, table=True):
    id: str = Field(
        default_factory=generate_uuid_id,
        primary_key=True,
        index=True
    )
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    checkins: List["WorkshopCheckin"] = Relationship(back_populates="workshop")


class WorkshopCreate(BaseWorkshop):
    pass


class WorkshopRead(BaseWorkshop):
    id: str
    created_at: datetime

class WorkshopReadAll(BaseWorkshop):
    id: str
    created_at: datetime


class WorkshopUpdate(SQLModel):
    name: Optional[str] = Field(default=None)
    alias: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    dtstart: Optional[datetime] = Field(default=None)
    dtend: Optional[datetime] = Field(default=None)
    place: Optional[str] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class WorkshopCheckin(SQLModel, table=True):
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    workshop_id: str = Field(foreign_key="workshop.id", primary_key=True)
    user: Optional["Users"] = Relationship(back_populates="checkins")
    workshop: Optional["Workshop"] = Relationship(back_populates="checkins")