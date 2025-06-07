from contextlib import asynccontextmanager

from fastapi import FastAPI

import os

from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

from src.storages.sql.dependencies import create_db_and_table

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_table()
    yield
