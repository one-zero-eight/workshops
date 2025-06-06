from contextlib import asynccontextmanager

from fastapi import FastAPI

import os

from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(
    url=os.getenv("WURL", "sqlite:///./tasks.db"),
    echo=True
)


def create_db_and_table():
    SQLModel.metadata.create_all(engine)


def get_session():
    # ensures that db is opened and closed per request
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    yield
