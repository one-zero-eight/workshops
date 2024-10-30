__all__ = ["CreateUserScheme", "ViewUserScheme"]


from src.pydantic_base import BaseSchema


class CreateUserScheme(BaseSchema):
    innohassle_id: str
    email: str
    name: str | None = None


class ViewUserScheme(BaseSchema):
    id: int
    innohassle_id: str
    email: str
    name: str | None = None
