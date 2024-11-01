__all__ = ["lifespan"]

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

import src.storages.sql.storage
from src.config import settings
from src.modules.innohassle_accounts import innohassle_accounts


async def setup_repositories(app):
    async_engine = create_async_engine(settings.database_uri.get_secret_value())
    app.state.storage = src.storages.sql.storage.SQLAlchemyStorage(async_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_repositories(app)
    await innohassle_accounts.update_key_set()
    yield
    from src.storages.sql.storage import storage

    await storage.close_connection()
