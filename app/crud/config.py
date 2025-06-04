import os

from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from app.models.user import Users

load_dotenv()

engine = create_engine(
    url = os.getenv("WURL", "sqlite:///./tasks.db"),
    echo=True
)

def create_db_and_table():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    #ensures that db is opened and closed per request
    with Session(engine) as session:
        yield session