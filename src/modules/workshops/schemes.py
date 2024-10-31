import datetime

from pydantic import BaseModel, Field, NaiveDatetime, model_validator

_now = datetime.datetime.now().replace(second=0, microsecond=0, tzinfo=None)


class ViewWorkshopScheme(BaseModel):
    id: int
    name: str
    alias: str
    description: str
    dtstart: datetime.datetime
    dtend: datetime.datetime
    capacity: int
    remain_places: int


class CreateWorkshopScheme(BaseModel):
    name: str
    alias: str
    description: str
    capacity: int

    dtstart: NaiveDatetime = Field(example=_now)
    dtend: NaiveDatetime = Field(example=_now)

    @model_validator(mode="after")
    def order_times(self):
        if self.dtstart >= self.dtend:
            raise ValueError("`dtstart` must be less than `dtend`")
        return self
