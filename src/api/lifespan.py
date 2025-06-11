from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.modules.innohassle_accounts import innohassle_accounts
from src.storages.sql.dependencies import create_db_and_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_table()
    await innohassle_accounts.update_key_set()
    yield
