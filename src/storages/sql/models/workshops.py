__all__ = ["Workshop", "CheckIn"]

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.storages.sql.models.base import Base


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    dtstart: Mapped[datetime.datetime] = mapped_column(DateTime)
    dtend: Mapped[datetime.datetime] = mapped_column(DateTime)

    capacity: Mapped[int] = mapped_column()
    remain_places: Mapped[int] = mapped_column()

    check_ins = relationship("CheckIn", back_populates="workshop")


class CheckIn(Base):
    __tablename__ = "workshops_checkins"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workshop_id: Mapped[int] = mapped_column(Integer, ForeignKey("workshops.id", ondelete="CASCADE"), primary_key=True)
    workshop = relationship("Workshop", back_populates="check_ins")
    user = relationship("User", back_populates="check_ins")
