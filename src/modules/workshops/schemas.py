from datetime import UTC, datetime

from pydantic import field_validator, model_validator
from sqlmodel import SQLModel


class CreateWorkshopScheme(SQLModel):
    name: str
    description: str
    capacity: int | None = 500
    remain_places: int | None = 500
    place: str

    dtstart: datetime
    dtend: datetime

    is_active: bool | None = False
    is_registrable: bool | None = False

    @model_validator(mode="after")
    def validate_workshops_in_the_past(self):
        current_time = datetime.now(UTC)
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
    description: str | None
    dtstart: datetime
    dtend: datetime
    place: str | None
    capacity: int
    remain_places: int
    is_active: bool
    is_registrable: bool


class UpdateWorkshopScheme(SQLModel):
    name: str | None = None
    description: str | None = None
    dtstart: datetime | None = None
    dtend: datetime | None = None
    place: str | None = None
    capacity: int | None = None
    is_active: bool | None = None
    is_registrable: bool | None = None

    @model_validator(mode="after")
    def validate_time(self):
        if self.dtstart is not None and self.dtend is not None:
            if self.dtstart >= self.dtend:
                raise ValueError("`dtstart` must be less than `dtend`")
        return self
