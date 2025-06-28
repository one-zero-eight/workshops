from datetime import datetime, timedelta

from sqlmodel import Relationship, SQLModel, Field

from pydantic import field_validator, model_validator

from typing import TYPE_CHECKING, List, Optional
from src.utils.utils import generate_uuid_id

if TYPE_CHECKING:
    from src.storages.sql.models.users import User


class Workshop(SQLModel, table=True):
    __tablename__ = "workshops"  # type: ignore

    "Unique identifier generated with UUID standard"
    id: str = Field(default_factory=generate_uuid_id, primary_key=True, index=True)

    "Human-readable name of the workshop, indexed for search"
    name: str = Field(index=True, max_length=255)

    "Optional textual description of the workshop"
    description: Optional[str] = Field(default=None)

    "Date and time when the workshop begins"
    dtstart: datetime

    "Date and time when the workshop ends (must be later than dtstart)"
    dtend: datetime

    "Optional location where the workshop takes place"
    place: Optional[str] = Field(default=None)

    "Maximum number of attendees allowed for the workshop"
    capacity: int = Field(ge=0, default=500)

    "Number of places still available; cannot exceed capacity"
    remain_places: int = Field(default=500, ge=0)

    "Marks whether the workshop is currently active (visible for users)"
    is_active: Optional[bool] = False

    "Marks whether users can register to the workshop"
    is_registrable: Optional[bool] = False

    "List of check-in records associated with this workshop"
    checkins: List["WorkshopCheckin"] = Relationship(
        back_populates="workshop",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    "Timestamp of when the workshop was created"
    created_at: datetime = Field(default_factory=datetime.now)

    "Clamp remain_places to not exceed capacity"

    @field_validator("remain_places")
    def clamp_remain_places(cls, remain_places, values):
        capacity = values.data["capacity"]
        if remain_places >= capacity:
            return capacity
        return remain_places

    "Validate that start time is before end time"

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self


class WorkshopCheckin(SQLModel, table=True):
    "Foreign key referencing user who checked in (part of primary key)"

    user_id: str = Field(
        foreign_key="users.id",
        primary_key=True,
        sa_column_kwargs={"on_delete": "CASCADE"},
    )

    "Foreign key referencing the workshop being checked into (part of primary key)"
    workshop_id: str = Field(
        foreign_key="workshops.id",
        primary_key=True,
        sa_column_kwargs={"on_delete": "CASCADE"},
    )

    "Reference to the associated user object"
    user: Optional["User"] = Relationship(back_populates="checkins")

    "Reference to the associated workshop object"
    workshop: Optional["Workshop"] = Relationship(back_populates="checkins")
