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
    
    is_active: Optional[bool] = False

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
    is_active: bool


class UpdateWorkshopScheme(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dtstart: Optional[datetime] = None
    dtend: Optional[datetime] = None
    place: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
