
from sqlmodel import SQLModel


from src.storages.sql.models.users import UserRole


class CreateUserSchemeOld(SQLModel):
    innohassle_id: str
    email: str
    name: str | None = None
    
class CreateUserScheme(SQLModel):
    innohassle_id: str


class ViewUserSchemeOld(SQLModel):
    id: str
    innohassle_id: str
    email: str
    name: str | None
    role: UserRole

class ViewUserScheme(SQLModel):
    id: str
    innohassle_id: str
    email: str
    name: str | None
    role: UserRole