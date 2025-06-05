from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlmodel import Session, select, update
from typing import List, Annotated, Sequence

from datetime import datetime, timedelta


from app.crud.config import get_session
from app.api.routes import users
from app.models.user import Users
from app.models.workshop import Workshop, BaseWorkshop, WorkshopRead, WorkshopCreate, WorkshopUpdate, WorkshopReadAll
from app.models.check_in import WorkshopCheckin

router = APIRouter(prefix="/api/workshops")


def get_workshop_or_404(session: Session, workshop_id: str) -> Workshop:
    workshop = session.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop


def get_workshops_for_user(session: Session, user_id: str) -> Sequence[Workshop]:
    statement = select(Workshop).join(WorkshopCheckin).where(
        WorkshopCheckin.user_id == user_id)

    results = session.exec(statement)
    return results.all()


def validate_checkin_conditions(session: Session, user: Users, workshop: Workshop):
    if not workshop.is_active:
        raise HTTPException(
            status_code=400, detail="This workshop is not active")
    if workshop.remain_places <= 0:
        raise HTTPException(
            status_code=400, detail="No available places left in this workshop.")
    if workshop.dtstart >= datetime.now() + timedelta(days=1):
        raise HTTPException(
            status_code=400, detail="This workshop will start in more than 1 day")

    checked_in_workshops = get_workshops_for_user(session, user.id)
    for other in checked_in_workshops:
        if other.dtstart <= workshop.dtend and workshop.dtstart <= other.dtend:
            raise HTTPException(
                status_code=400, detail="This workshop overlaps with another you're already checked in to.")


@router.post("/", response_model=WorkshopRead, status_code=status.HTTP_201_CREATED)
async def add_workshop(*,
                       session: Session = Depends(get_session),
                       workshop: WorkshopCreate,
                       _: Annotated[Users, Depends(users.is_admin)]):
    db_workshop = Workshop.model_validate(workshop)

    session.add(db_workshop)
    session.commit()
    session.refresh(db_workshop)

    return db_workshop


@router.get("/{workshop_id}", response_model=WorkshopRead)
async def get_workshop_details(
    *,
    session: Session = Depends(get_session),
    workshop_id: str
):
    return get_workshop_or_404(session, workshop_id)


@router.get("/", response_model=List[WorkshopReadAll])
async def get_all_workshops(
    *,
    session: Session = Depends(get_session),
    limit: int = 100,
):
    query = select(Workshop)
    return session.exec(query.limit(limit=limit))


@router.put("/{workshop_id}")
async def update_workshop(
    workshop_id: str,
    workshop: WorkshopUpdate,
    session: Session = Depends(get_session)
):
    db_workshop = get_workshop_or_404(session, workshop_id)

    workshop_dump = workshop.model_dump()
    for key, value in workshop_dump.items():
        if value is not None:
            setattr(db_workshop, key, value)

    session.add(db_workshop)
    session.commit()
    session.refresh(db_workshop)

    return {"message": "Workshop updated successfully"}


@router.delete("/{workshop_id}")
async def delete_workshop(workshop_id: str,
                          _: Annotated[Users, Depends(users.is_admin)],
                          session: Session = Depends(get_session)
                          ):
    db_workshop = get_workshop_or_404(session, workshop_id)

    session.delete(db_workshop)
    session.commit()
    return {"message": "Workshop deleted successfully"}


@router.post("/checkin/{workshop_id}")
async def checkin_user(
    workshop_id: str,
    user: Annotated[Users, Depends(users.get_current_user)],
    session: Session = Depends(get_session)
):
    db_workshop = get_workshop_or_404(session, workshop_id)

    existing = session.get(WorkshopCheckin, (user.id, workshop_id))
    if existing:
        raise HTTPException(status_code=400,
                            detail="User is already checked in to this workshop")
    
    validate_checkin_conditions(session, user, db_workshop)

    checkin = WorkshopCheckin(user_id=user.id, workshop_id=workshop_id)
    session.add(checkin)

    db_workshop.remain_places -= 1
    session.add(db_workshop)

    session.commit()
    session.refresh(db_workshop)
    session.refresh(checkin)

    return {
        "message": "User checked in successfully",
        "workshop_id": workshop_id,
        "available_places": db_workshop.remain_places
    }


@router.post("/checkout/{workshop_id}")
async def checkout_user(
    workshop_id: str,
    user: Annotated[Users, Depends(users.get_current_user)],
    session: Session = Depends(get_session)
):
    db_workshop = get_workshop_or_404(session, workshop_id)

    existing_checkin = session.get(WorkshopCheckin, (user.id, workshop_id))
    if not existing_checkin:
        raise HTTPException(status_code=404, detail="User is not checked in to this workshop")

    if db_workshop.remain_places + 1 > db_workshop.capacity:
        raise HTTPException(status_code=400, detail="Cannot exceed workshop capacity")

    db_workshop.remain_places += 1
    session.add(db_workshop)
    session.delete(db_workshop)

    session.commit()
    session.refresh(db_workshop)

    return {
        "message": "User checked out successfully",
        "workshop_id": workshop_id,
        "available_places": db_workshop.remain_places
    }
