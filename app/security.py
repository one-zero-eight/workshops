from passlib.context import CryptContext
from datetime import timedelta, datetime
from app.api.routes import users
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def create_acess_token(subject: str, expires_delta: timedelta):
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, users.SECRET_KEY, users.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
