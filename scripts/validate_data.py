"""
Database data validation script.
Validates all existing database records against Pydantic models.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.storages.sql.dependencies import Session
from src.storages.sql.models import User, Workshop, WorkshopCheckin


async def validate_users(session: AsyncSession) -> tuple[int, list[dict[str, Any]]]:
    """Validate all User records."""
    result = await session.execute(select(User))
    users = result.scalars().all()

    errors = []
    for user in users:
        try:
            User.model_validate(user.model_dump())
        except Exception as e:
            errors.append(
                {
                    "table": "users",
                    "id": user.innohassle_id,
                    "error": str(e),
                }
            )

    return len(users), errors


async def validate_workshops(session: AsyncSession) -> tuple[int, list[dict[str, Any]]]:
    """Validate all Workshop records."""
    result = await session.execute(select(Workshop))
    workshops = result.scalars().all()

    errors = []
    for workshop in workshops:
        try:
            Workshop.model_validate(workshop.model_dump())
        except Exception as e:
            errors.append(
                {
                    "table": "workshops",
                    "id": workshop.id,
                    "english_name": workshop.english_name,
                    "error": str(e),
                }
            )

    return len(workshops), errors


async def validate_checkins(session: AsyncSession) -> tuple[int, list[dict[str, Any]]]:
    """Validate all WorkshopCheckin records."""
    result = await session.execute(select(WorkshopCheckin))
    checkins = result.scalars().all()

    errors = []
    for checkin in checkins:
        try:
            WorkshopCheckin.model_validate(checkin.model_dump())
        except Exception as e:
            errors.append(
                {
                    "table": "workshop_checkins",
                    "user_id": checkin.user_id,
                    "workshop_id": checkin.workshop_id,
                    "error": str(e),
                }
            )

    return len(checkins), errors


async def main():
    print("=" * 60)
    print("Starting database validation...")
    print(f"Database URL: {settings.db_url.get_secret_value().split('@')[-1]}")
    print("=" * 60)

    all_errors = []
    total_records = 0

    async with Session() as session:
        print("\nValidating Users...")
        user_count, user_errors = await validate_users(session)
        total_records += user_count
        all_errors.extend(user_errors)
        print(f"✓ Validated {user_count} users ({len(user_errors)} errors)")

        print("\nValidating Workshops...")
        workshop_count, workshop_errors = await validate_workshops(session)
        total_records += workshop_count
        all_errors.extend(workshop_errors)
        print(f"✓ Validated {workshop_count} workshops ({len(workshop_errors)} errors)")

        print("\nValidating Workshop Check-ins...")
        checkin_count, checkin_errors = await validate_checkins(session)
        total_records += checkin_count
        all_errors.extend(checkin_errors)
        print(f"✓ Validated {checkin_count} check-ins ({len(checkin_errors)} errors)")

    print("\n" + "=" * 60)
    print(f"Total records validated: {total_records}")
    print(f"Total errors found: {len(all_errors)}")

    if all_errors:
        print("\n⚠️  VALIDATION FAILED - Errors found:")
        print("-" * 60)
        for i, error in enumerate(all_errors, 1):
            print(f"\n{i}. Table: {error['table']}")
            if "id" in error:
                print(f"   ID: {error['id']}")
            if "english_name" in error:
                print(f"   Name: {error['english_name']}")
            if "user_id" in error:
                print(f"   User ID: {error['user_id']}")
            if "workshop_id" in error:
                print(f"   Workshop ID: {error['workshop_id']}")
            print(f"   Error: {error['error']}")
        print("\n" + "=" * 60)
        return 1
    else:
        print("\n✅ All records are valid!")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
