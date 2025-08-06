from sqlmodel import SQLModel

from src.storages.sql.models import UserRole


class CreateUserScheme(SQLModel):
    innohassle_id: str
    email: str
    telegram_username: str | None


class ViewUserScheme(SQLModel):
    id: str
    innohassle_id: str
    role: UserRole
    email: str
    telegram_username: str | None
    "Will be shown only for admins"
