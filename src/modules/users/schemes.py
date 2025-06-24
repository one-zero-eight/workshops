
from sqlmodel import SQLModel


from src.storages.sql.models.users import UserRole


class CreateUserScheme(SQLModel):
    innohassle_id: str
    email: str


class ViewUserScheme(SQLModel):
    id: str
    innohassle_id: str
    role: UserRole
    email: str