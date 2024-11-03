from enum import Enum


class CheckInEnum(Enum):
    SUCCESS = "Success"
    ALREADY_CHECKED_IN = "You already checked in this workshop"
    WORKSHOP_DOES_NOT_EXIST = "Workshop does not exist"
    NO_PLACES = "No places available"
    INVALID_TIME = "You can not check in this workshop now"
    CHECK_IN_DOES_NOT_EXIST = "You did not check in this workshop"


class WorkshopEnum(Enum):
    CREATED = "Created"
    ALIAS_ALREADY_EXISTS = "Alias already exists"
