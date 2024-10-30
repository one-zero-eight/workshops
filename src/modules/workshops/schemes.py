import datetime

from pydantic import BaseModel


class ViewWorkshopScheme(BaseModel):
    id: int
    name: str
    alias: str
    description: str
    dtstart: datetime.datetime
    dtend: datetime.datetime
    capacity: int
    remain_places: int
