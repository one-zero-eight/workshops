from enum import Enum


class RegistrationEnum(Enum):
    SUCCESS = "Success"
    NOT_ACTIVE = "Event is not active"
    ALREADY_REGISTERED = "You already registered for this event"
    EVENT_DOES_NOT_EXIST = "Event does not exist"
    NO_PLACES = "No places available"
    INVALID_TIME = "You cannot register for this event yet"
    TIME_IS_OVER = "The time for this event is over"
    OVERLAPPING_EVENTS = "You have overlapping events"
    REGISTRATION_DOES_NOT_EXIST = "You did not register for this event"


class EventEnum(Enum):
    CREATED = "Succesfully created the event"
    UPDATED = "Succesfully updated the event"
    INVALID_CAPACITY_FOR_UPDATE = "Capacity cannot be less than current number of registered users"
    EVENT_DOES_NOT_EXIST = "Event does not exist"
    DELETED = "Succesfully deleted the event"
