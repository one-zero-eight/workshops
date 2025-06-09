from datetime import datetime

from sqlmodel import SQLModel

from pydantic import model_validator

from typing import Optional


class CreateWorkshopScheme(SQLModel):
    name: str
    description: str
    capacity: int
    remain_places: Optional[int] = 501
    place: str

    dtstart: datetime
    dtend: datetime

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self


class ReadWorkshopScheme(SQLModel):
    id: str
    name: str
    description: Optional[str]
    dtstart: datetime
    dtend: datetime
    place: Optional[str]
    capacity: int
    remain_places: int


class UpdateWorkshopScheme(SQLModel):
    name: Optional[str]
    alias: Optional[str]
    description: Optional[str]
    dtstart: Optional[datetime]
    dtend: Optional[datetime]
    place: Optional[str]
    capacity: Optional[int]
    is_active: Optional[bool]
