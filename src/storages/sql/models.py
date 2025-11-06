import datetime
import re
import uuid
from enum import StrEnum
from typing import cast

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import column_property
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from sqlmodel._compat import SQLModelConfig


def utcnow():
    return datetime.datetime.now(datetime.UTC)


class UserRole(StrEnum):
    admin = "admin"
    user = "user"


class WorkshopLanguage(StrEnum):
    english = "english"
    russian = "russian"


HEX6 = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Badge(BaseModel):
    title: str
    color: str

    @field_validator("title")
    @classmethod
    def non_empty_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        if len(v) > 40:
            raise ValueError("title too long")
        return v

    @field_validator("color")
    @classmethod
    def hex_color(cls, v: str) -> str:
        if not HEX6.fullmatch(v):
            raise ValueError("color must be hex #RRGGBB")
        return v


class Base(SQLModel):
    model_config = cast(SQLModelConfig, ConfigDict(json_schema_serialization_defaults_required=True))


class User(Base, table=True):
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


class Workshop(Base, table=True):
    __tablename__ = "workshops"  # type: ignore

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    "Unique identifier generated with UUID standard"
    english_name: str = Field(index=True, max_length=255)
    "Human-readable name of the workshop in English, indexed for search"
    russian_name: str = Field(index=True, max_length=255)
    "Human-readable name of the workshop in Russian, also indexed for search"
    english_description: str | None = None
    "Optional textual description of the workshop in English"
    russian_description: str | None = None
    "Optional textual description of the workshop in Russian"
    language: WorkshopLanguage = Field(...)
    "Language of the workshop"
    host: str
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop begins"
    dtend: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime = Field(sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int = Field(default=10**6)
    "Maximum number of attendees allowed for the workshop"
    badges: list[dict[str, str]] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    "List of badges associated with this workshop"
    is_active: bool = True
    "Marks whether the workshop is currently active (visible for users)"
    is_draft: bool = False
    "Marks whether the workshop is currently in draft phase (visible only for author)"
    checkins: list["WorkshopCheckin"] = Relationship(back_populates="workshop", cascade_delete=True)
    "List of check-in records associated with this workshop"
    created_at: datetime.datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True)))
    "Timestamp of when the workshop was created"

    @computed_field
    def remain_places(self) -> int:
        return self.capacity - self._checkins_count

    @computed_field
    def is_registrable(self) -> bool:
        """
        Marks whether users can register to the workshop.
        ~~Can be register only within 1 day before the workshop~~, and cannot be register after the workshop.
        """
        _now = datetime.datetime.now(datetime.UTC)
        if _now > self.dtend:
            return False
        # if self.dtstart - _now > datetime.timedelta(days=1):
        #     return False  # Can check in only 1 day before
        return True

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        if self.check_in_opens is not None and self.check_in_opens >= self.dtstart:
            raise ValueError("`check_in_opens` must be less than `dtstart`")
        return self


class CreateWorkshop(Base):
    english_name: str = Field(..., max_length=255)
    "Human-readable name of the workshop in English, indexed for search"
    russian_name: str = Field(..., max_length=255)
    "Human-readable name of the workshop in Russian, also indexed for search"
    english_description: str | None = None
    "Optional textual description of the workshop in English"
    russian_description: str | None = None
    "Optional textual description of the workshop in Russian"
    language: WorkshopLanguage
    "Language of the workshop"
    host: str
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime
    "Date and time when the workshop begins"
    dtend: datetime.datetime
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime | None = None
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int | None = None
    "Maximum number of attendees allowed for the workshop"
    is_draft: bool | None = None
    "Marks whether the workshop is currently in draft phase (visible only for author)"
    badges: list[Badge] = list
    "List of badges associated with this workshop"

    @model_validator(mode="before")
    @classmethod
    def validate_time(cls, data: dict):
        if data.get("dtstart") is None:
            raise ValueError("`dtstart` is missing")
        if data.get("dtend") is None:
            raise ValueError("`dtend` is missing")
        if data["dtstart"] >= data["dtend"]:
            raise ValueError("`dtstart` must be less than `dtend`")
        if data.get("check_in_opens") is not None and data["check_in_opens"] >= data["dtstart"]:
            raise ValueError("`check_in_opens` must be less than `dtstart`")
        return data

    @model_validator(mode="after")
    def set_check_in_opens_default(self):
        if self.check_in_opens is None and self.dtstart is not None:
            self.check_in_opens = self.dtstart - datetime.timedelta(days=1)
        return self


class UpdateWorkshop(Base):
    english_name: str | None = None
    "Human-readable name of the workshop in English"
    russian_name: str | None = None
    "Human-readable name of the workshop in Russian"
    english_description: str | None = None
    "Optional textual description of the workshop in English"
    russian_description: str | None = None
    "Optional textual description of the workshop in Russian"
    language: WorkshopLanguage | None = None
    "Language of the workshop"
    host: str | None = None
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime | None = None
    "Date and time when the workshop begins"
    dtend: datetime.datetime | None = None
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime | None
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int | None = None
    "Maximum number of attendees allowed for the workshop"
    badges: list[Badge] | None = None
    "List of badges associated with this workshop"
    is_active: bool | None = None
    "Marks whether the workshop is currently active (visible for users)"
    is_draft: bool | None = None
    "Marks whether the workshop is currently in draft phase (visible only for author)"

    @model_validator(mode="before")
    @classmethod
    def validate_time(cls, data: dict):
        if data.get("dtstart") is None and data.get("dtend") is None:
            return data
        if data.get("dtstart") is None or data.get("dtend") is None:
            raise ValueError("`dtstart` and `dtend` must be provided")
        if data["dtstart"] >= data["dtend"]:
            raise ValueError("`dtstart` must be less than `dtend`")
        if data["check_in_opens"] >= data["dtstart"]:
            raise ValueError("`check_in_opens` must be less than `dtstart`")
        return data


class WorkshopCheckin(Base, table=True):
    user_id: str = Field(foreign_key="users.innohassle_id", primary_key=True, ondelete="CASCADE")
    "Foreign key referencing user who checked in (part of primary key)"
    workshop_id: str = Field(foreign_key="workshops.id", primary_key=True, ondelete="CASCADE")
    "Foreign key referencing the workshop being checked into (part of primary key)"
    user: User | None = Relationship(back_populates="checkins")
    "Reference to the associated user object"
    workshop: Workshop | None = Relationship(back_populates="checkins")
    "Reference to the associated workshop object"


Workshop._checkins_count = column_property(
    select(func.count(WorkshopCheckin.user_id))
    .where(WorkshopCheckin.workshop_id == Workshop.id)
    .correlate(Workshop)  # explicitly correlate with Workshop table
    .scalar_subquery()
)
