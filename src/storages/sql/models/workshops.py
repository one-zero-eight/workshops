__all__ = ["Workshop", "CheckIn"]

import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.storages.sql.models.base import Base


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    dtstart: Mapped[datetime.datetime] = mapped_column()
    dtend: Mapped[datetime.datetime] = mapped_column()

    capacity: Mapped[int] = mapped_column()


class CheckIn(Base):
    __tablename__ = "workshops_checkins"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
