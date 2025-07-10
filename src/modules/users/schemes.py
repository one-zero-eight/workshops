from sqlmodel import SQLModel


from src.storages.sql.models.users import UserRole


class CreateUserScheme(SQLModel):
    innohassle_id: str
    email: str
    t_alias: str


class ViewUserScheme(SQLModel):
    id: str
    innohassle_id: str
    role: UserRole
    email: str
    alias: str
