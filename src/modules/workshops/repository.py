from sqlmodel import Session, select
from typing import Sequence

from datetime import datetime, timedelta

from src.modules.workshops.schemes import WorkshopCheckin, Workshop, WorkshopCreate, WorkshopUpdate
from src.modules.users.schemes import Users

from src.modules.workshops.enums import WorkshopEnum, CheckInEnum   


class WorkshopRepository:
    def __init__(self, session: Session):
        self.session = session

    # TODO: Check whether it should return none
    async def create_workshop(self, workshop: WorkshopCreate) -> tuple[Workshop | None, WorkshopEnum]:
        db_workshop = Workshop.model_validate(workshop)

        self.session.add(db_workshop)
        self.session.commit()
        self.session.refresh(db_workshop)

        return db_workshop, WorkshopEnum.CREATED
    
    async def get_all_workshops(self, limit: int = 100) -> Sequence[Workshop]:
        query = select(Workshop)
        workshops = self.session.exec(query.limit(limit=limit))
        return workshops.all()

    async def get_workshop_by_id(self, workshop_id: str) -> Workshop | None:
        query = select(Workshop).where(Workshop.id == workshop_id)
        workshop = self.session.exec(query).first()
        return workshop

    async def update_workshop(self, workshop_id: str, workshop_update: WorkshopUpdate) -> Workshop | None:
        workshop = await self.get_workshop_by_id(workshop_id)
        if workshop:
            workshop_dump = workshop.model_dump()
            for key, value in workshop_dump.items():
                if value is not None:
                    setattr(workshop, key, value)
        
            self.session.add(workshop)
            self.session.commit()
            self.session.refresh(workshop)
        
        return workshop
    
    async def change_active_status_workshop(self, workshop_id: str, active: bool) -> Workshop | None:
        workshop = await self.get_workshop_by_id(workshop_id)
        if not workshop:
            return None
        
        workshop.is_active = active
        workshop.remain_places = workshop.capacity  # Reset remaining places to capacity
    
        self.session.add(workshop)
        self.session.commit()
        self.session.refresh(workshop)
        
        return workshop


    async def delete_workshop(self, workshop_id: str) -> WorkshopEnum:
        workshop = await self.get_workshop_by_id(workshop_id)
        
        if not workshop:
            return WorkshopEnum.WORKSHOP_DOES_NOT_EXIST
        
        self.session.delete(workshop)
        self.session.commit()
        
        return WorkshopEnum.DELETED



class CheckInRepository:
    def __init__(self, session: Session, workshop_repo: WorkshopRepository):
        self.session = session
        self.workshop_repo = workshop_repo

    async def exists_checkin(self, user_id: str, workshop_id: str) -> bool:
        existing = self.session.get(WorkshopCheckin, (user_id, workshop_id))
        if existing is not None:
            return True
        return False

    async def create_checkIn(self, user_id: str, workshop_id: str) -> CheckInEnum:
        workshop = await self.workshop_repo.get_workshop_by_id(workshop_id)

        if not workshop:
            return CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        if not workshop.is_active:
            return CheckInEnum.NOT_ACTIVE
        if workshop.remain_places <= 0:
            return CheckInEnum.NO_PLACES
        if workshop.dtstart >= datetime.now() + timedelta(days=1):
            return CheckInEnum.INVALID_TIME

        #TODO: Fix bug here with checking in
        if await self.exists_checkin(user_id, workshop_id):
            return CheckInEnum.ALREADY_CHECKED_IN

        checked_in_workshops = await self.get_checked_in_workshops_for_user(user_id)
        for other in checked_in_workshops:
            if other.dtstart <= workshop.dtend and workshop.dtstart <= other.dtend:
                return CheckInEnum.OVERLAPPING_WORKSHOPS

        checkin = WorkshopCheckin(user_id=user_id, workshop_id=workshop.id)
        self.session.add(checkin)
        self.session.commit()
        self.session.refresh(checkin)

        workshop.remain_places -= 1
        self.session.add(workshop)
        self.session.commit()

        return CheckInEnum.SUCCESS

    async def remove_checkIn(self, user_id: str, workshop_id: str) -> CheckInEnum:
        workshop = await self.workshop_repo.get_workshop_by_id(workshop_id)

        if not workshop:
            return CheckInEnum.WORKSHOP_DOES_NOT_EXIST

        if not await self.exists_checkin(user_id, workshop_id):
            return CheckInEnum.CHECK_IN_DOES_NOT_EXIST

        checkin = self.session.get(WorkshopCheckin, (user_id, workshop_id))
        self.session.delete(checkin)
        self.session.commit()

        workshop.remain_places += 1
        self.session.add(workshop)
        self.session.commit()

        return CheckInEnum.SUCCESS

    async def get_checked_in_workshops_for_user(self, user_id: str) -> Sequence[Workshop]:
        statement = select(Workshop).join(WorkshopCheckin).where(
            WorkshopCheckin.user_id == user_id)

        results = self.session.exec(statement)
        return results.all()

    async def get_checked_in_users_for_workshop(self, workshop_id: str) -> Sequence[Users]:
        statement = select(Users).join(WorkshopCheckin).where(
            WorkshopCheckin.workshop_id == workshop_id)
        return self.session.exec(statement).all()
