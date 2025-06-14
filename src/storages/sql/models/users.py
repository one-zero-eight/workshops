from enum import Enum

from sqlmodel import Relationship, SQLModel, Field


from typing import TYPE_CHECKING, List, Optional
from src.utils.utils import generate_uuid_id


if TYPE_CHECKING:
    from src.storages.sql.models.workshops import WorkshopCheckin


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore
    "Unique identiefied generated with UUID standard"
    id: str = Field(default_factory=generate_uuid_id, primary_key=True)
    "InnoHassle identifier"
    innohassle_id: str = Field(default="someid")

    role: UserRole = Field(default=UserRole.user)

    "All checkins for specific user "
    checkins: List["WorkshopCheckin"] = Relationship(
        back_populates="user",     sa_relationship_kwargs={"cascade": "all, delete-orphan"})
