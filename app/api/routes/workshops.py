from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlmodel import Session, select, update
from typing import List, Annotated

from app.crud.config import get_session
from app.api.routes import users
from app.models.user import Users
from app.models.workshop import Workshop, BaseWorkshop, WorkshopRead, WorkshopCreate, WorkshopUpdate
from app.models.check_in import CheckIns

router = APIRouter(prefix="/api/workshops")


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


@router.get("/", response_model=List[WorkshopRead])
async def get_all_workshops(
    *,
    session: Session = Depends(get_session),
    limit: int = 100,
):
    query = select(Workshop)
    tasks = session.exec(query.limit(limit=limit))
    return tasks


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
    return {"message": "succesfully deleted user"}

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDkwMzYyMjQsInN1YiI6IjYzNzEyYjM5LWRjNGQtNDg5Yi1iYmVjLWZmMzdmZjFkMGVhMiJ9.MEA1-gc4llpqbLW-XdLDHyWWh-IbE6NeQyiFAWtaTMk


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

    existing = session.get(CheckIns, (user.id, workshop_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User already checked in"
        )

    if workshop.available_places <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available places left in this workshop."
        )

    # Decrement available places
    checkin = CheckIns(user_id=user.id, workshop_id=workshop_id)
    session.add(checkin)

    workshop.available_places -= 1
    session.add(workshop)

    session.commit()
    session.refresh(workshop)
    session.refresh(checkin)

    return {
        "message": "User checked in successfully",
        "workshop_id": workshop_id,
        "available_places": workshop.available_places
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

    existing = session.get(CheckIns, (user.id, workshop_id))
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not checked in"
        )

    if workshop.available_places + 1 > workshop.max_places:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit of places was reached"
        )

    # Decrement available places
    workshop.available_places += 1
    session.add(workshop)
    session.delete(existing)

    session.commit()
    session.refresh(workshop)

    return {
        "message": "User checked out successfully",
        "workshop_id": workshop_id,
        "available_places": workshop.available_places
    }


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

    return {"message": "changed attributes"}


'''
POST   /api/workshops/          # Create a workshop under the event +
GET    /workshops/{workshop_id}               # Get details of a specific workshop +
DELETE /workshops/{workshop_id}               # Delete a workshop +
PUT    /workshops/{workshop_id}               # Update a workshop 
POST   /workshops/{workshop_id}/checkin     # Check in a participant + 
POST   /workshops/{workshop_id}/checkout      # Check in a participant +
'''
