from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.crud import config
from app.routes import workshops
from app.routes import users

import os

from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        create_engine)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.create_db_and_table()
    yield
    
app = FastAPI(
    title="Task Management API",
    description="API for managing tasks with FastAPI, SQLModel, and Pydantic",
    version="0.1.0",
    lifespan=lifespan
)


app.include_router(workshops.router)
app.include_router(users.router)


@app.get("/")
async def root():
    """Health check endpoint for the API."""
    return {"message": "Welcome to the Task Management API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
