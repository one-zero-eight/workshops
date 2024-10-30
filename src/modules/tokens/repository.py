__all__ = ["TokenRepository"]

import time

from authlib.jose import JoseError, JWTClaims, jwt
from pydantic import BaseModel

from src.modules.innohassle_accounts import innohassle_accounts
from src.modules.users.repository import SqlUserRepository
from src.modules.users.schemes import CreateUserScheme


class UserTokenData(BaseModel):
    user_id: int
    innohassle_id: str


class TokenRepository:
    def __init__(self, user_repository: SqlUserRepository) -> None:
        self.user_repository = user_repository

    def decode_token(self, token: str) -> JWTClaims:
        now = time.time()
        pub_key = innohassle_accounts.get_public_key()
        payload = jwt.decode(token, pub_key)
        payload.validate_exp(now, leeway=0)
        payload.validate_iat(now, leeway=0)
        return payload

    async def fetch_user_id_or_create(self, innohassle_id: str) -> int | None:
        user_id = await self.user_repository.read_id_by_innohassle_id(innohassle_id)
        if user_id is not None:
            return user_id

        innohassle_user = await innohassle_accounts.get_user_by_id(innohassle_id)
        if innohassle_user is None:
            return None

        user = CreateUserScheme(
            innohassle_id=innohassle_id,
            email=innohassle_user.innopolis_sso.email,
            name=innohassle_user.innopolis_sso.name,
        )
        user_id = (await self.user_repository.create(user)).id
        return user_id

    async def verify_user_token(self, token: str, credentials_exception) -> UserTokenData:
        try:
            payload = self.decode_token(token)
            innohassle_id: str = payload.get("uid")
            if innohassle_id is None:
                raise credentials_exception
            user_id = await self.fetch_user_id_or_create(innohassle_id)
            if user_id is None:
                raise credentials_exception
            return UserTokenData(user_id=user_id, innohassle_id=innohassle_id)
        except JoseError:
            raise credentials_exception
