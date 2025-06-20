from datetime import datetime

from sqlmodel import SQLModel

from pydantic import field_validator, model_validator

from typing import Optional


class CreateWorkshopScheme(SQLModel):
    name: str
    description: str
    capacity: Optional[int] = 500
    remain_places: Optional[int] = 500
    place: str

    dtstart: datetime
    dtend: datetime

    is_active: Optional[bool] = False
    is_registrable: Optional[bool] = False

    @model_validator(mode="after")
    def validate_workshops_in_the_past(self):
        current_time = datetime.now()
        if current_time > self.dtstart:
            raise ValueError("Cannot create workshops in the past")
        return self

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self

    @field_validator("dtstart")
    def remove_microseconds_dtstart(cls, dtstart):
        return dtstart.replace(microsecond=0) 
    
    @field_validator("dtend")
    def remove_microseconds_dtend(cls, dtend):
        return dtend.replace(microsecond=0) 


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
    is_registrable: bool


class UpdateWorkshopScheme(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dtstart: Optional[datetime] = None
    dtend: Optional[datetime] = None
    place: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    is_registrable: Optional[bool] = None
    
    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart is not None and self.dtend is not None:
            if self.dtstart >= self.dtend: 
                raise ValueError("`dtstart` must be less than `dtend`")
        return self
    
