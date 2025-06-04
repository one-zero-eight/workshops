from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.crud import config
from app.api.routes import workshops
from app.api.routes import users
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, UploadFile, File
from app.services import excel_parser


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

templates = Jinja2Templates(directory=".")


app.include_router(workshops.router)
app.include_router(users.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def download(file: UploadFile = File(...)):
    content = await file.read()
    content_type = str(file.filename).split(".")[-1]
    
    with open(f"handle.{content_type}", "wb") as f:
        f.write(content)

    return "hello"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
