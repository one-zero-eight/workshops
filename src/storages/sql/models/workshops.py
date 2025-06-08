from datetime import datetime

from sqlmodel import Relationship, SQLModel, Field

from pydantic import field_validator, model_validator

from typing import TYPE_CHECKING, List, Optional
from src.utils.utils import generate_uuid_id

if TYPE_CHECKING:
    from src.storages.sql.models.users import User


class Workshop(SQLModel, table=True):
    __tablename__ = "workshops" # type: ignore
    
    id: str = Field(
        default_factory=generate_uuid_id,
        primary_key=True,
        index=True
    )
    
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None)
    
    dtstart: datetime
    dtend: datetime
    
    place: Optional[str] = Field(default=None)
    
    capacity: int = Field(ge=0, default=500)
    remain_places: int = Field(default=501, ge=0)

    is_active: Optional[bool] = False

    checkins: List["WorkshopCheckin"] = Relationship(back_populates="workshop")
    created_at: datetime = Field(default_factory=datetime.now)
    
    #TODO: Fix Kostyli
    @field_validator("remain_places")
    def clamp_remain_places(cls, remain_places, values):
        capacity = values.data["capacity"]
        if remain_places > capacity:
            return capacity
        return remain_places
    
    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self


class WorkshopCheckin(SQLModel, table=True):
    # __tablename__: str == "checkins" # type: ignore
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    workshop_id: str = Field(foreign_key="workshops.id", primary_key=True)
    user: Optional["User"] = Relationship(back_populates="checkins")
    workshop: Optional["Workshop"] = Relationship(back_populates="checkins")