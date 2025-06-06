from passlib.context import CryptContext
from datetime import timedelta, datetime
from src.modules.workshops import dependencies
from jose import jwt


pwd_context = CryptContext(schemes=["argon2"])

def create_acess_token(subject: str, expires_delta: timedelta):
    expire = datetime.now() + expires_delta
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, dependencies.SECRET_KEY, dependencies.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
