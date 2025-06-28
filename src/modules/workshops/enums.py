from enum import Enum


class CheckInEnum(Enum):
    SUCCESS = "Success"
    NOT_ACTIVE = "Workshop is not active"
    ALREADY_CHECKED_IN = "You already checked in this workshop"
    WORKSHOP_DOES_NOT_EXIST = "Workshop does not exist"
    NO_PLACES = "No places available"
    INVALID_TIME = "You can not check in this workshop now"
    OVERLAPPING_WORKSHOPS = "You have overlapping workshops"
    CHECK_IN_DOES_NOT_EXIST = "You did not check in this workshop"


class WorkshopEnum(Enum):
    CREATED = "Succesfully created the workshop"
    UPDATED = "Succesfully updated the workshop"
    INVALID_CAPACITY_FOR_UPDATE = (
        "Capacity cannot be less than current number of checked in users"
    )
    WORKSHOP_DOES_NOT_EXIST = "Workshop does not exist"
    DELETED = "Succesfully updated the workshop"
