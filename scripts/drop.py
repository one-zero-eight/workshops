# autodrop_sqlmodel.py
from sqlmodel import SQLModel
import os

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.config import settings

import asyncio
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine

# Do not remove here these imports
from src.storages.sql.models.workshops import Workshop, WorkshopCheckin
from src.storages.sql.models.users import User

engine = create_async_engine(settings.database_uri, echo=True)


async def drop_all():
    print("Dropping all (students from uni) tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    print("All (students) tables dropped!")


if __name__ == "__main__":
    asyncio.run(drop_all())
