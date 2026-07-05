import asyncio

import magic
from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

import src.modules.events.minio as minio
from src.api.dependencies import (
    CurrentUserDep,
    EventRepositoryDep,
    OptionalCurrentUserDep,
)
from src.config import settings
from src.logging_ import logger
from src.modules.clubs.dependencies import get_user_clubs
from src.modules.events.enums import EventEnum, RegistrationEnum
from src.modules.events.utils import is_leader_of_club
from src.modules.inh_accounts_sdk import inh_accounts
from src.modules.users.schemas import ViewUserScheme
from src.storages.sql.models import CreateEvent, Event, EventStatus, UpdateEvent, UserRole

router = APIRouter(prefix="/events", tags=["Events"])


def convert_image_to_webp(bytes_: bytes) -> bytes:
    import pyvips

    image: pyvips.Image = pyvips.Image.new_from_buffer(bytes_, "")
    return image.write_to_buffer(".webp")


async def can_edit_event(event: Event, user: CurrentUserDep) -> bool:
    if user.role == UserRole.ADMIN or user.email in settings.superadmin_emails:
        return True
    if event.created_by == user.innohassle_id:
        return True

    # Check if user is leader of a club hosting this event
    try:
        user_clubs = await get_user_clubs(user)
        if is_leader_of_club(user_clubs, event.host):
            return True
    except Exception as e:
        logger.warning(f"Failed to fetch user clubs: {e}")

    return False


async def filter_visible_events(events: list[Event], user: OptionalCurrentUserDep) -> list[Event]:
    if user and (user.role == UserRole.ADMIN or user.email in settings.superadmin_emails):
        return events

    visible_events = []

    # Pre-fetch clubs if user is authenticated to avoid fetching per event
    user_clubs = []
    if user:
        try:
            user_clubs = await get_user_clubs(user)
        except Exception as e:
            logger.warning(f"Failed to fetch user clubs: {e}")

    for event in events:
        if event.status == EventStatus.APPROVED:
            visible_events.append(event)
        elif user:
            if event.created_by == user.innohassle_id or is_leader_of_club(user_clubs, event.host):
                visible_events.append(event)

    return visible_events


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Event successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Event creation failed"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
    },
)
async def add_event(
    event_repo: EventRepositoryDep,
    event_create: CreateEvent,
    user: CurrentUserDep,
) -> Event:
    """
    Create a new event. The event will start in 'draft' status.
    """
    user_clubs = await get_user_clubs(user)
    if (
        not is_leader_of_club(user_clubs, event_create.host)
        and not user.role == UserRole.ADMIN
        and user.email not in settings.superadmin_emails
    ):
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can add events with other clubs as hosts. You can create "
            f"events with following clubs as host: {[user_club.title for user_club in user_clubs]}",
        )

    event, operation_status = await event_repo.create(event_create, created_by=user.innohassle_id)
    if operation_status != EventEnum.CREATED:
        raise HTTPException(status_code=400, detail=operation_status.value)
    if not event:
        raise HTTPException(status_code=400, detail="Event creation failed")
    return event


@router.get(
    "/",
    responses={
        status.HTTP_200_OK: {"description": "Events retrieved successfully"},
    },
)
async def get_all_events(
    event_repo: EventRepositoryDep,
    user: OptionalCurrentUserDep,
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = Query(
        None, description="Comma-separated list of statuses (e.g. draft,pending_review,approved)"
    ),
) -> list[Event]:
    """
    List events. By default, only approved events are returned.
    Authenticated users can specify statuses to see their own non-approved events.
    """
    statuses = None
    if status:
        statuses = [EventStatus(s.strip()) for s in status.split(",") if s.strip()]

    events = await event_repo.get_all(limit=limit, statuses=statuses)

    # Filter by visibility rules
    visible_events = await filter_visible_events(list(events), user)
    return visible_events


@router.get(
    "/{event_id}",
    responses={
        status.HTTP_200_OK: {"description": "Event retrieved successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found or not visible"},
    },
)
async def get_event(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: OptionalCurrentUserDep,
) -> Event:
    """
    Get a single event by ID.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    visible_events = await filter_visible_events([event], user)
    if not visible_events:
        raise HTTPException(status_code=404, detail="Event not found")

    return visible_events[0]


@router.patch(
    "/{event_id}",
    responses={
        status.HTTP_200_OK: {"description": "Event updated successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def update_event(
    event_id: str,
    event_update: UpdateEvent,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> Event:
    """
    Partially update an event. If the event was approved, it will be moved back to 'draft'.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not await can_edit_event(event, user):
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")

    # Extra check if changing hosts
    if event_update.host is not None:
        user_clubs = await get_user_clubs(user)
        if not is_leader_of_club(user_clubs, event_update.host) and not user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Only admins can edit events with other clubs as hosts. You can edit "
                f"events with following clubs as host: {[user_club.title for user_club in user_clubs]}",
            )

    updated_event, operation_status = await event_repo.update(event_id, event_update)

    if not updated_event:
        raise HTTPException(status_code=404, detail=operation_status.value)
    if operation_status != EventEnum.UPDATED:
        raise HTTPException(status_code=400, detail=operation_status.value)
    return updated_event


@router.post(
    "/{event_id}/publish",
    responses={
        status.HTTP_200_OK: {"description": "Event submitted for review"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def publish_event(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> Event:
    """
    Submit an event for review. Changes status from 'draft' or 'rejected' to 'pending_review'.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not await can_edit_event(event, user):
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")

    if event.status not in [EventStatus.DRAFT, EventStatus.REJECTED]:
        raise HTTPException(status_code=400, detail=f"Event cannot be published from status '{event.status.value}'")

    # Ensure required fields are present
    if not event.dtstart or not event.dtend or not event.language:
        raise HTTPException(
            status_code=400,
            detail="Event is missing required fields (dtstart, dtend, language) and cannot be published.",
        )

    updated_event, operation_status = await event_repo.publish(event_id)
    if not updated_event:
        raise HTTPException(status_code=404, detail=operation_status.value)
    return updated_event


@router.post(
    "/{event_id}/approve",
    responses={
        status.HTTP_200_OK: {"description": "Event approved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Only superadmin can approve events"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def approve_event(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> Event:
    """
    Approve an event, making it visible to the public.
    """
    if user.email not in settings.superadmin_emails:
        raise HTTPException(status_code=403, detail="Only superadmin can approve events")

    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != EventStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail=f"Event cannot be approved from status '{event.status.value}'")

    updated_event, operation_status = await event_repo.approve(event_id)
    if not updated_event:
        raise HTTPException(status_code=404, detail=operation_status.value)
    return updated_event


@router.post(
    "/{event_id}/reject",
    responses={
        status.HTTP_200_OK: {"description": "Event rejected successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Only superadmin can reject events"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def reject_event(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> Event:
    """
    Reject an event. Changes status to 'rejected' so the creator can edit and resubmit.
    """
    if user.email not in settings.superadmin_emails:
        raise HTTPException(status_code=403, detail="Only superadmin can reject events")

    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != EventStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail=f"Event cannot be rejected from status '{event.status.value}'")

    updated_event, operation_status = await event_repo.reject(event_id)
    if not updated_event:
        raise HTTPException(status_code=404, detail=operation_status.value)
    return updated_event


@router.delete(
    "/{event_id}",
    responses={
        status.HTTP_200_OK: {"description": "Event deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
    },
)
async def delete_event(
    event_id: str,
    user: CurrentUserDep,
    event_repo: EventRepositoryDep,
):
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not await can_edit_event(event, user):
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")

    operation_status = await event_repo.delete(event_id)
    if operation_status != EventEnum.DELETED:
        logger.error(f"Failed during deleting event. Status: {operation_status}")
        raise HTTPException(status_code=404, detail=operation_status.value)

    return {"message": EventEnum.DELETED.value}


@router.post(
    "/{event_id}/registrations",
    responses={
        status.HTTP_200_OK: {"description": "User successfully registered"},
        status.HTTP_400_BAD_REQUEST: {"description": "Some error occurred during registration"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def register_user(
    event_id: str,
    user: CurrentUserDep,
    event_repo: EventRepositoryDep,
) -> None:
    """
    Register a user for an event.
    """
    registration_status = await event_repo.register(user.innohassle_id, event_id)
    if registration_status == RegistrationEnum.EVENT_DOES_NOT_EXIST:
        raise HTTPException(status_code=404, detail=registration_status.value)
    elif registration_status != RegistrationEnum.SUCCESS:
        raise HTTPException(status_code=400, detail=registration_status.value)
    return None


@router.delete(
    "/{event_id}/registrations",
    responses={
        status.HTTP_200_OK: {"description": "User successfully unregistered"},
        status.HTTP_400_BAD_REQUEST: {"description": "Some error occurred during unregistration"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def unregister_user(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
):
    """
    Unregister a user from an event.
    """
    remove_registration_status = await event_repo.unregister(user.innohassle_id, event_id)
    if remove_registration_status == RegistrationEnum.EVENT_DOES_NOT_EXIST:
        raise HTTPException(status_code=404, detail=remove_registration_status.value)
    elif remove_registration_status != RegistrationEnum.SUCCESS:
        raise HTTPException(status_code=400, detail=remove_registration_status.value)
    return None


@router.get(
    "/{event_id}/registrations",
    responses={
        status.HTTP_200_OK: {"description": "All registrations retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def get_all_registrations(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> list[ViewUserScheme]:
    """
    Get all registered users for an event. Non-admins get a redacted view.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    users = await event_repo.get_registered_users(event_id)
    validated = [ViewUserScheme.model_validate(u) for u in users]

    if user.role != UserRole.ADMIN:
        for u in validated:
            u.telegram_username = None  # set to None for non-admins to avoid leaking info
            u.name = None
    else:
        user_info_tasks = [inh_accounts.get_user(email=u.email) for u in validated]
        user_infos = await asyncio.gather(*user_info_tasks, return_exceptions=True)

        for u, user_info in zip(validated, user_infos):
            if isinstance(user_info, BaseException):
                continue
            if user_info and user_info.innopolis_info:
                u.name = user_info.innopolis_info.name
    return validated


@router.get(
    "/{event_id}/image",
    responses={
        status.HTTP_307_TEMPORARY_REDIRECT: {"description": "Redirect to the event image"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found or no logo available"},
    },
    response_model=None,
)
async def get_event_image(
    event_id: str,
    event_repo: EventRepositoryDep,
):
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not event.image_file_id:
        raise HTTPException(status_code=404, detail="No image available")

    url = await run_in_threadpool(minio.get_event_picture_url, event.image_file_id)
    return RedirectResponse(url=url)


@router.put(
    "/{event_id}/image",
    responses={
        status.HTTP_200_OK: {"description": "Changed event image successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid content type"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized to change event image"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def set_event_image(
    event_id: str,
    image_file: UploadFile,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
) -> Event:
    """
    Upload or replace an event image. Doing this to an approved event resets it to draft.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not await can_edit_event(event, user):
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")

    bytes_ = await image_file.read()
    content_type = image_file.content_type
    if content_type is None:
        content_type = magic.Magic(mime=True).from_buffer(bytes_)

    supported_content_types = ["image/jpeg", "image/png", "image/webp"]
    if content_type not in supported_content_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid content type ({content_type}), must be one of {supported_content_types}"
        )

    image_bytes = await run_in_threadpool(convert_image_to_webp, bytes_)

    # Save file
    image_file_id = event_id
    await run_in_threadpool(minio.put_event_picture, image_file_id, image_bytes, "image/webp")
    updated_event, _ = await event_repo.update_image_file_id(event_id, image_file_id)
    return updated_event or event


@router.delete(
    "/{event_id}/image",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Deleted event image successfully"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized to change event image"},
        status.HTTP_404_NOT_FOUND: {"description": "Event not found"},
    },
)
async def delete_event_image(
    event_id: str,
    event_repo: EventRepositoryDep,
    user: CurrentUserDep,
):
    """
    Delete an event image. Doing this to an approved event resets it to draft.
    """
    event = await event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not await can_edit_event(event, user):
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")

    if not event.image_file_id:
        raise HTTPException(status_code=404, detail="No image available")

    await run_in_threadpool(minio.delete_event_picture, event.image_file_id)
    await event_repo.update_image_file_id(event_id, None)
