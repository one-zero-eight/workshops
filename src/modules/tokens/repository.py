__all__ = ["TokenRepository"]

import time

from authlib.jose import JWTClaims, jwt, JoseError


from src.modules.innohassle_accounts import innohassle_accounts
from src.modules.users.repository import UsersRepository
from src.modules.innohassle_accounts import innohassle_accounts
from src.modules.users.schemes import CreateUserScheme
from sqlmodel import SQLModel
from src.logging import logger


class UserTokenData(SQLModel):
    user_id: str
    innohassle_id: str


class TokenRepository:
    PUBLIC_KID = "public"

    def __init__(self, user_repository: UsersRepository) -> None:
        self.user_repository = user_repository

    def decode_token(self, token: str) -> JWTClaims:
        now = time.time()
        pub_key = innohassle_accounts.get_public_key()

        payload = jwt.decode(token, pub_key)
        payload.validate_exp(now, leeway=0)
        payload.validate_iat(now, leeway=0)
        return payload

    async def fetch_user_id_or_create(self, innohassle_id: str) -> str | None:
        user_id = await self.user_repository.read_id_by_innohassle_id(innohassle_id)
        if user_id is not None:
            return user_id

        logger.info("User not found. Attempting to create user")
        
        user = CreateUserScheme(
            innohassle_id=innohassle_id,
        )
        user_id = (await self.user_repository.create(user)).id
        return user_id

    async def verify_user_token(self, token: str, credentials_exception) -> UserTokenData:
        try:
            payload = self.decode_token(token)
        
            innohassle_id: str = payload.get("uid")  # type:ignore

            logger.info(f"uid == None: {payload.get("uid") == None}.\n")
            if innohassle_id is None:
                innohassle_id = payload.get("scope")  # type:ignore
                logger.warning(f"scope == None: {payload.get("scope") == None} Used service token.")
                if innohassle_id is None:
                    raise credentials_exception
                innohassle_id = innohassle_id[6:]

            user_id = await self.fetch_user_id_or_create(innohassle_id)
            if user_id is None: 
                logger.warning("User_Id not found")               
                raise credentials_exception
            return UserTokenData(user_id=user_id, innohassle_id=innohassle_id)
        except JoseError as e:
            logger.error(f"JoseError: {e}")
            raise credentials_exception
