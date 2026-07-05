from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.logging_ import logger
from src.modules.events.enums import EventEnum, RegistrationEnum
from src.storages.sql.models import CreateEvent, Event, EventRegistration, EventStatus, UpdateEvent, User


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _detach_and_close_transaction(self, *objects: object | None) -> None:
        for obj in objects:
            if obj is None:
                continue
            try:
                self.session.expunge(obj)
            except InvalidRequestError:
                pass
        if self.session.in_transaction():
            await self.session.rollback()

    async def create(self, event: CreateEvent, created_by: str) -> tuple[Event | None, EventEnum]:
        if not event.capacity:
            event.capacity = 10**6
        db_event = Event.model_validate(
            {**event.model_dump(exclude_unset=True), "status": EventStatus.DRAFT, "created_by": created_by}
        )

        self.session.add(db_event)
        await self.session.commit()
        await self.session.refresh(db_event)
        await self._detach_and_close_transaction(db_event)

        return db_event, EventEnum.CREATED

    async def get_all(
        self, limit: int = 100, statuses: list[EventStatus] | None = None, close_transaction: bool = True
    ) -> Sequence[Event]:
        query = select(Event)
        if statuses:
            query = query.where(Event.status.in_(statuses))
        result = await self.session.execute(query.limit(limit=limit))
        events = list(result.scalars().all())
        if close_transaction:
            await self._detach_and_close_transaction(*events)
        return events

    async def get(self, event_id: str, close_transaction: bool = True) -> Event | None:
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        event = result.scalars().first()
        if close_transaction:
            await self._detach_and_close_transaction(event)
        return event

    async def update(self, event_id: str, event_update: UpdateEvent) -> tuple[Event | None, EventEnum]:
        event = await self.get(event_id, close_transaction=False)
        if not event:
            await self._detach_and_close_transaction()
            return None, EventEnum.EVENT_DOES_NOT_EXIST

        logger.info(f"Updating event data. Current data: {event}")

        current_data = event.model_dump()
        update_data = event_update.model_dump(exclude_unset=True)

        if "dtstart" in update_data:
            new_start = update_data["dtstart"]

            if "check_in_opens" not in update_data:
                update_data["check_in_opens"] = new_start - timedelta(days=1)

            if "check_in_closes" not in update_data:
                update_data["check_in_closes"] = new_start

        # If it was approved, reset to draft
        if event.status == EventStatus.APPROVED:
            update_data["status"] = EventStatus.DRAFT

        merged_data = {**current_data, **update_data}

        Event.model_validate(merged_data)

        if event_update.capacity is not None:
            current_registrations = event.capacity - event.remain_places
            if event_update.capacity < current_registrations:
                await self._detach_and_close_transaction(event)
                return None, EventEnum.INVALID_CAPACITY_FOR_UPDATE
            event.capacity = event_update.capacity

        for key, value in update_data.items():
            if value is not None:
                setattr(event, key, value)

        await self.session.commit()
        await self.session.refresh(event)
        await self._detach_and_close_transaction(event)

        logger.info(f"Updated event data. New data: {event}")

        return event, EventEnum.UPDATED

    async def publish(self, event_id: str) -> tuple[Event | None, EventEnum]:
        event = await self.get(event_id, close_transaction=False)
        if not event:
            await self._detach_and_close_transaction()
            return None, EventEnum.EVENT_DOES_NOT_EXIST

        event.status = EventStatus.PENDING_REVIEW

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        await self._detach_and_close_transaction(event)

        return event, EventEnum.UPDATED

    async def approve(self, event_id: str) -> tuple[Event | None, EventEnum]:
        event = await self.get(event_id, close_transaction=False)
        if not event:
            await self._detach_and_close_transaction()
            return None, EventEnum.EVENT_DOES_NOT_EXIST

        event.status = EventStatus.APPROVED

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        await self._detach_and_close_transaction(event)

        return event, EventEnum.UPDATED

    async def reject(self, event_id: str) -> tuple[Event | None, EventEnum]:
        event = await self.get(event_id, close_transaction=False)
        if not event:
            await self._detach_and_close_transaction()
            return None, EventEnum.EVENT_DOES_NOT_EXIST

        event.status = EventStatus.REJECTED

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        await self._detach_and_close_transaction(event)

        return event, EventEnum.UPDATED

    async def delete(self, event_id: str) -> EventEnum:
        event = await self.get(event_id, close_transaction=False)

        if not event:
            await self._detach_and_close_transaction()
            return EventEnum.EVENT_DOES_NOT_EXIST

        await self.session.delete(event)
        await self.session.commit()

        return EventEnum.DELETED

    async def is_registered(self, user_id: str, event_id: str, close_transaction: bool = True) -> bool:
        existing = await self.session.get(EventRegistration, (user_id, event_id))
        if close_transaction:
            await self._detach_and_close_transaction(existing)
        if existing is not None:
            return True
        return False

    async def register(self, user_id: str, event_id: str) -> RegistrationEnum:
        event = await self.get(event_id, close_transaction=False)

        if not event:
            await self._detach_and_close_transaction()
            return RegistrationEnum.EVENT_DOES_NOT_EXIST

        if event.status != EventStatus.APPROVED:
            await self._detach_and_close_transaction(event)
            return RegistrationEnum.NOT_ACTIVE

        if event.remain_places <= 0:
            await self._detach_and_close_transaction(event)
            return RegistrationEnum.NO_PLACES

        if event.dtstart < datetime.now(UTC):
            await self._detach_and_close_transaction(event)
            return RegistrationEnum.TIME_IS_OVER

        if await self.is_registered(user_id, event_id, close_transaction=False):
            await self._detach_and_close_transaction(event)
            return RegistrationEnum.ALREADY_REGISTERED

        registered_events = await self.get_registered_events(user_id, close_transaction=False)
        for other in registered_events:  # block only overlap more than 1 minute
            if other.dtend < event.dtstart:
                continue
            elif other.dtstart > event.dtend:
                continue
            else:
                overlap_start = max(other.dtstart, event.dtstart)
                overlap_end = min(other.dtend, event.dtend)
                if overlap_end - overlap_start > timedelta(minutes=1):
                    await self._detach_and_close_transaction(event, *registered_events)
                    return RegistrationEnum.OVERLAPPING_EVENTS

        registration = EventRegistration(user_id=user_id, event_id=event.id)
        self.session.add(registration)
        await self.session.commit()
        await self.session.refresh(registration)
        await self._detach_and_close_transaction(registration)

        return RegistrationEnum.SUCCESS

    async def unregister(self, user_id: str, event_id: str) -> RegistrationEnum:
        event = await self.get(event_id, close_transaction=False)

        if not event:
            await self._detach_and_close_transaction()
            return RegistrationEnum.EVENT_DOES_NOT_EXIST

        if not await self.is_registered(user_id, event_id, close_transaction=False):
            await self._detach_and_close_transaction(event)
            return RegistrationEnum.REGISTRATION_DOES_NOT_EXIST

        registration = await self.session.get(EventRegistration, (user_id, event_id))
        await self.session.delete(registration)
        await self.session.commit()

        return RegistrationEnum.SUCCESS

    async def get_registered_events(self, user_id: str, close_transaction: bool = True) -> Sequence[Event]:
        statement = select(Event).join(EventRegistration).where(EventRegistration.user_id == user_id)
        results = await self.session.execute(statement)
        events = list(results.scalars().all())
        if close_transaction:
            await self._detach_and_close_transaction(*events)
        return events

    async def get_registered_users(self, event_id: str, close_transaction: bool = True) -> Sequence[User]:
        statement = select(User).join(EventRegistration).where(EventRegistration.event_id == event_id)
        result = await self.session.execute(statement)
        users = list(result.scalars().all())
        if close_transaction:
            await self._detach_and_close_transaction(*users)
        return users

    async def update_image_file_id(self, event_id: str, image_file_id: str | None) -> tuple[Event | None, EventEnum]:
        event = await self.get(event_id, close_transaction=False)
        if not event:
            await self._detach_and_close_transaction()
            return None, EventEnum.EVENT_DOES_NOT_EXIST

        event.image_file_id = image_file_id
        if event.status == EventStatus.APPROVED:
            event.status = EventStatus.DRAFT

        await self.session.commit()
        await self.session.refresh(event)
        await self._detach_and_close_transaction(event)
        return event, EventEnum.UPDATED
