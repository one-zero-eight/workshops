import datetime
import uuid
from enum import StrEnum

from pydantic import field_validator, model_validator
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel


def utcnow():
    return datetime.datetime.now(datetime.UTC)


class UserRole(StrEnum):
    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore
    innohassle_id: str = Field(primary_key=True)
    "InNoHassle Accounts ID"
    email: str
    "Innopolis email (@innopolis.university or @innopolis.ru)"
    telegram_username: str | None
    "Telegram alias of user. If user is not presented in InNoHassle system will be None"
    role: UserRole = Field(default=UserRole.user)
    "Role of user"
    checkins: list["WorkshopCheckin"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    "All checkins for specific user"

    @property
    def id(self) -> str:
        """Alias for innohassle_id to maintain compatibility with ViewUserScheme"""
        return self.innohassle_id


class Workshop(SQLModel, table=True):
    __tablename__ = "workshops"  # type: ignore
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    "Unique identifier generated with UUID standard"
    name: str = Field(index=True, max_length=255)
    "Human-readable name of the workshop, indexed for search"
    description: str | None = Field(default=None)
    "Optional textual description of the workshop"
    dtstart: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop begins"
    dtend: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop ends (must be later than dtstart)"
    place: str | None = Field(default=None)
    "Optional location where the workshop takes place"
    capacity: int = Field(ge=0, default=500)
    "Maximum number of attendees allowed for the workshop"
    remain_places: int = Field(default=500, ge=0)
    "Number of places still available; cannot exceed capacity"
    is_active: bool | None = False
    "Marks whether the workshop is currently active (visible for users)"
    is_registrable: bool | None = False
    "Marks whether users can register to the workshop"
    checkins: list["WorkshopCheckin"] = Relationship(back_populates="workshop", cascade_delete=True)
    "List of check-in records associated with this workshop"
    created_at: datetime.datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True)))
    "Timestamp of when the workshop was created"

    @field_validator("remain_places")
    def clamp_remain_places(cls, remain_places, values):
        capacity = values.data["capacity"]
        if remain_places >= capacity:
            return capacity
        return remain_places

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self


class WorkshopCheckin(SQLModel, table=True):
    user_id: str = Field(foreign_key="users.innohassle_id", primary_key=True, ondelete="CASCADE")
    "Foreign key referencing user who checked in (part of primary key)"
    workshop_id: str = Field(foreign_key="workshops.id", primary_key=True, ondelete="CASCADE")
    "Foreign key referencing the workshop being checked into (part of primary key)"
    user: User | None = Relationship(back_populates="checkins")
    "Reference to the associated user object"
    workshop: Workshop | None = Relationship(back_populates="checkins")
    "Reference to the associated workshop object"
