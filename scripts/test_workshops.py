# autodrop_sqlmodel.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storages.sql.models.workshops import Workshop, WorkshopCheckin
from src.storages.sql.models.users import User
from src.modules.workshops.schemes import CreateWorkshopScheme

from src.config import settings
from sqlmodel import SQLModel, insert



engine = create_async_engine(settings.database_uri._secret_value, echo=True)

now = datetime.now()
create_data = [
    CreateWorkshopScheme(
        name="Python Basics",
        description="Introductory course on Python",
        place="Room A",
        capacity=500,
        remain_places=500,
        dtstart=now + timedelta(days=1, hours=9),
        dtend=now + timedelta(days=1, hours=11),
        is_active=False,
    ),
    CreateWorkshopScheme(
        name="Advanced SQL",
        description="Deep dive into SQL optimization and joins",
        place="Room B",
        capacity=40,
        remain_places=35,
        dtstart=now + timedelta(days=2, hours=14),
        dtend=now + timedelta(days=2, hours=17),
        is_active=True,
    ),
    CreateWorkshopScheme(
        name="Docker & Deployment",
        description="Containerizing and deploying Python apps",
        place="Room C",
        capacity=25,
        remain_places=25,
        dtstart=now + timedelta(days=3, hours=10),
        dtend=now + timedelta(days=3, hours=12),
        is_active=False,
    ),
]

workshops: list[Workshop] = [Workshop.model_validate(data) for data in create_data]

print(workshops)

async def create_test_workshops():
    print("Creating 3 new workshops...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        for ws in workshops:
            ins = insert(Workshop).values(ws.model_dump())
            await conn.execute(ins)
        await conn.commit()
    print("3 workshops sucessfully added")

if __name__ == "__main__":
    asyncio.run(create_test_workshops())
