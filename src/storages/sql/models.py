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
    ADMIN = "admin"
    USER = "user"


class WorkshopLanguage(StrEnum):
    ENGLISH = "english"
    RUSSIAN = "russian"
    BOTH = "both"


class CheckInType(StrEnum):
    NO_CHECK_IN = "no_check_in"
    ON_INNOHASSLE = "on_innohassle"
    BY_LINK = "by_link"


class HostType(StrEnum):
    CLUB = "club"
    OTHER = "other"


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


class Link(BaseModel):
    title: str
    url: str

    @field_validator("title")
    @classmethod
    def non_empty_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        if len(v) > 40:
            raise ValueError("title too long")
        return v

    @field_validator("url")
    @classmethod
    def non_empty_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url cannot be empty")
        return v


class Host(BaseModel):
    host_type: HostType
    name: str

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
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
    role: UserRole = Field(default=UserRole.USER)
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
    language: WorkshopLanguage | None = Field(None)
    "Language of the workshop"
    host: list[dict[str, str]] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime | None = Field(None, sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop begins"
    dtend: datetime.datetime | None = Field(None, sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime | None = Field(None, sa_column=Column(DateTime(timezone=True)))
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int | None = Field(None)
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
    links: list[dict[str, str]] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    "List of links associated with this workshop"
    check_in_type: CheckInType = Field(
        CheckInType.ON_INNOHASSLE,
        sa_column=Column(sa.Enum(CheckInType), nullable=False, server_default=CheckInType.ON_INNOHASSLE.value),
    )
    "Type of check-in (No check-in, on InNoHassle, or by link)"
    check_in_link: str | None = None
    "Link for check-in, if check-in type is 'by link'"
    is_active: bool = True
    "Marks whether the workshop is currently active (visible for users)"
    is_draft: bool = False
    "Marks whether the workshop is currently in draft phase (visible only for author)"
    image_file_id: str | None = None
    "File ID of the event image"
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
        Can register after check-in opens dt, and cannot register after the workshop.
        Cannot register to drafts.
        """
        if self.is_draft:
            return False
        _now = datetime.datetime.now(datetime.UTC)
        if _now > self.dtend:
            return False
        if _now < self.check_in_opens:
            return False
        return True

    @model_validator(mode="after")
    def validate_time(self):
        if self.is_draft:
            return self  # No need to validate drafts
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        if self.check_in_opens is not None and self.check_in_opens >= self.dtstart:
            raise ValueError("`check_in_opens` must be less than `dtstart`")
        return self

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: dict):
        if data.get("is_draft"):
            return data  # No need to validate drafts
        if data.get("language") is None:
            raise ValueError("`language` is missing")
        if data.get("dtstart") is None:
            raise ValueError("`dtstart` is missing")
        if data.get("dtend") is None:
            raise ValueError("`dtend` is missing")
        if data.get("check_in_type") == CheckInType.BY_LINK and (
            data.get("check_in_link") is None or data.get("check_in_link") == ""
        ):
            raise ValueError("`check_in_link` is missing")
        return data


class CreateWorkshop(Base):
    english_name: str = Field(..., max_length=255)
    "Human-readable name of the workshop in English, indexed for search"
    russian_name: str = Field(..., max_length=255)
    "Human-readable name of the workshop in Russian, also indexed for search"
    english_description: str | None = None
    "Optional textual description of the workshop in English"
    russian_description: str | None = None
    "Optional textual description of the workshop in Russian"
    language: WorkshopLanguage | None = None
    "Language of the workshop"
    host: list[Host] | None = None
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime | None = None
    "Date and time when the workshop begins"
    dtend: datetime.datetime | None = None
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime | None = None
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int | None = None
    "Maximum number of attendees allowed for the workshop"
    is_draft: bool = False
    "Marks whether the workshop is currently in draft phase (visible only for author)"
    badges: list[Badge] = Field(default_factory=list)
    "List of badges associated with this workshop"
    links: list[Link] = Field(default_factory=list)
    "List of links associated with this workshop"
    check_in_type: CheckInType = Field(CheckInType.ON_INNOHASSLE)
    "Type of check-in (No check-in, on InNoHassle, or by link)"
    check_in_link: str | None = None
    "Link for check-in, if check-in type is 'by link'"

    @model_validator(mode="before")
    @classmethod
    def validate_time(cls, data: dict):
        if data.get("is_draft"):
            return data  # No need to validate drafts
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

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: dict):
        if data.get("is_draft"):
            return data  # No need to validate drafts
        if data.get("language") is None:
            raise ValueError("`language` is missing")
        if data.get("dtstart") is None:
            raise ValueError("`dtstart` is missing")
        if data.get("dtend") is None:
            raise ValueError("`dtend` is missing")
        if data.get("check_in_type") == CheckInType.BY_LINK and (
            data.get("check_in_link") is None or data.get("check_in_link") == ""
        ):
            raise ValueError("`check_in_link` is missing")
        return data


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
    host: list[Host] | None = None
    "Host of the workshop (e.g. some club)"
    dtstart: datetime.datetime | None = None
    "Date and time when the workshop begins"
    dtend: datetime.datetime | None = None
    "Date and time when the workshop ends (must be later than dtstart)"
    check_in_opens: datetime.datetime | None = None
    "Date and time when the workshop check-in starts. dtstart - 1 day by default"
    place: str | None = None
    "Optional location where the workshop takes place"
    capacity: int | None = None
    "Maximum number of attendees allowed for the workshop"
    badges: list[Badge] | None = None
    "List of badges associated with this workshop"
    links: list[Link] | None = None
    "List of links associated with this workshop"
    check_in_type: CheckInType | None = None
    "Type of check-in (No check-in, on InNoHassle, or by link)"
    check_in_link: str | None = None
    "Link for check-in, if check-in type is 'by link'"
    is_active: bool | None = None
    "Marks whether the workshop is currently active (visible for users)"
    is_draft: bool | None = None
    "Marks whether the workshop is currently in draft phase (visible only for author)"

    @model_validator(mode="before")
    @classmethod
    def validate_time(cls, data: dict):
        if data.get("is_draft"):
            return data  # No need to validate drafts
        if data.get("dtstart") is None and data.get("dtend") is None:
            return data
        if data.get("dtstart") is None or data.get("dtend") is None:
            raise ValueError("`dtstart` and `dtend` must be provided")
        if data["dtstart"] >= data["dtend"]:
            raise ValueError("`dtstart` must be less than `dtend`")
        if data.get("check_in_opens") is not None and data["check_in_opens"] >= data["dtstart"]:
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
