from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import Relationship, SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import TYPE_CHECKING, List, Optional
# from app.models.check_in import WorkshopCheckin
# from app.models.check_in import WorkshopCheckin
from app.utils.utils import generate_uuid_id

if TYPE_CHECKING:
    from .check_in import WorkshopCheckin


class BaseWorkshop(SQLModel):
    name: str = Field(index=True, max_length=255)
    alias: str = Field(max_length=255, unique=True)
    # description: Optional[str] = Field(default=None)
    dtstart: datetime
    # workshop_start_time: datetime = Field()
    dtend: datetime
    place: Optional[str] = Field(default=None)
    capacity: int
    remain_places: int = Field(default=10, ge=0)
    is_active: Optional[bool] = False


class Workshop(BaseWorkshop, table=True):
    id: str = Field(
        default_factory=generate_uuid_id,
        primary_key=True,
        index=True
    )
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
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

