from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import SQLModel, create_engine, Session, Field, Relationship
from datetime import timedelta
from app.models.workshop import Workshop
from app.models.user import Users


from typing import Optional
from app.utils.utils import generate_uuid_id

# class WorkshopCheckin(SQLModel, table=True):
#     user_id: str = Field(foreign_key="users.id", primary_key=True)
#     workshop_id: str = Field(foreign_key="workshop.id", primary_key=True)
#     workshop: Optional["Workshop"] = Relationship(back_populates="checkins")


class WorkshopCheckin(SQLModel, table=True):
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    workshop_id: str = Field(foreign_key="workshop.id", primary_key=True)
    user: Optional["Users"] = Relationship(back_populates="checkins")
    workshop: Optional["Workshop"] = Relationship(back_populates="checkins")