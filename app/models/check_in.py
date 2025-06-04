from datetime import datetime
from enum import Enum
import uuid

from sqlmodel import SQLModel, create_engine, Session, Field
from datetime import timedelta


from typing import Optional


class CheckIns(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    workshop_id: str = Field(primary_key=True)
