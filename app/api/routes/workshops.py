from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlmodel import Session, select, update
from typing import List, Annotated

from datetime import datetime, timedelta


from app.crud.config import get_session
from app.api.routes import users
from app.models.user import Users
from app.models.workshop import Workshop, BaseWorkshop, WorkshopRead, WorkshopCreate, WorkshopUpdate, WorkshopReadAll
from app.models.check_in import WorkshopCheckin

router = APIRouter(prefix="/api/workshops")


def get_workshops_for_user(session: Annotated[Session, Depends(get_session)], user_id: str):
    statement = select(Workshop).join(WorkshopCheckin).where(
        WorkshopCheckin.user_id == user_id)

    results = session.exec(statement)
    return results.all()


@router.post("/", response_model=WorkshopRead, status_code=status.HTTP_201_CREATED)
async def add_workshop(*,
                       session: Session = Depends(get_session),
                       workshop: WorkshopCreate,
                       user: Annotated[Users, Depends(users.is_admin)]):
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
    workshop = session.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    return workshop


@router.get("/", response_model=List[WorkshopReadAll])
async def get_all_workshops(
    *,
    session: Session = Depends(get_session),
    limit: int = 100,
):
    query = select(Workshop)
    tasks = session.exec(query.limit(limit=limit))

    return tasks


@router.put("/{workshop_id}")
async def update_workshop(
    workshop_id: str,
    workshop: WorkshopUpdate,
    session: Session = Depends(get_session)
):
    workshopDB = session.get(Workshop, workshop_id)

    if not workshopDB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workshop with ID {workshop_id} not found"
        )

    workshop_dump = workshop.model_dump()
    for key, value in workshop_dump.items():
        setattr(workshopDB, key, value)

    session.add(workshopDB)
    session.commit()
    session.refresh(workshopDB)

    return {"message": "Sucessfuly changed workshop"}


@router.delete("/{workshop_id}")
async def delete_workshop(workshop_id: str,
                          user: Annotated[Users, Depends(users.is_admin)],
                          session: Session = Depends(get_session)
                          ):
    db_workshop = session.get(Workshop, workshop_id)
    if not db_workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")

    session.delete(db_workshop)
    session.commit()
    return {"message": "Succesfully deleted workshop"}


@router.post("/checkin/{workshop_id}")
async def checkin_user(
    workshop_id: str,
    user: Annotated[Users, Depends(users.get_current_user)],
    session: Session = Depends(get_session)
):
    workshop = session.get(Workshop, workshop_id)

    if not workshop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workshop with ID {workshop_id} not found"
        )

    existing = session.get(WorkshopCheckin, (user.id, workshop_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User already checked in"
        )

    if workshop.remain_places <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available places left in this workshop."
        )

    checkedin_workshops = get_workshops_for_user(
        session=session, user_id=user.id)

    if workshop.dtstart >= datetime.now()+timedelta(days=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This workshop will start in more than 1 day"
        )

    for checkedin_workshop in checkedin_workshops:
        print(checkedin_workshop, workshop)
        if checkedin_workshop.dtstart <= workshop.dtend and workshop.dtstart <= checkedin_workshop.dtend:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This workshop coincides with workshop user already checked in"
            )

    checkin = WorkshopCheckin(user_id=user.id, workshop_id=workshop_id)
    session.add(checkin)

    workshop.remain_places -= 1
    session.add(workshop)

    session.commit()
    session.refresh(workshop)
    session.refresh(checkin)

    return {
        "message": "User checked in successfully",
        "workshop_id": workshop_id,
        "available_places": workshop.remain_places
    }


@router.post("/checkout/{workshop_id}")
async def checkout_user(
    workshop_id: str,
    user: Annotated[Users, Depends(users.get_current_user)],
    session: Session = Depends(get_session)
):
    workshop = session.get(Workshop, workshop_id)

    if not workshop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workshop with ID {workshop_id} not found"
        )

    existing = session.get(WorkshopCheckin, (user.id, workshop_id))
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not checked in"
        )

    if workshop.remain_places + 1 > workshop.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit of places was reached"
        )

    # Decrement available places
    workshop.remain_places += 1
    session.add(workshop)
    session.delete(existing)

    session.commit()
    session.refresh(workshop)

    return {
        "message": "User checked out successfully",
        "workshop_id": workshop_id,
        "available_places": workshop.remain_places
    }
